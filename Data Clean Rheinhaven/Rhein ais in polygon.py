import mysql.connector
import pandas as pd
from shapely.geometry import Polygon
import numpy as np


def get_and_save_ais_data_to_table():
    """
    Connects to a MySQL database, retrieves AIS data for a specific polygon,
    and saves it to a new table.
    """
    # --- Database Configuration ---
    # Make sure these details are correct for your local MySQL instance.
    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "AMS_ship_traj03",
        "database": "ship_data",
    }

    # --- Configuration ---
    source_table = "Rhein_ais_data"
    target_table = "Rhein_ais_data_polygon"

    # Polygon coordinates for the specified Rhine area.
    polygon_coords = [
        [8.261848723256719, 48.98288921678804],
        [8.263855823529667, 48.98107766698374],
        [8.273328288727953, 48.98614158405354],
        [8.28004155351249, 48.99021755756448],
        [8.286692213133449, 48.994993115901224],
        [8.283238834180793, 48.99626559181894],
        [8.281533583101549, 48.994297053149324],
        [8.278370189542017, 48.99194079979557],
        [8.272812540049557, 48.98851821906979],
        [8.261848723256719, 48.98288921678804],
    ]
    polygon = Polygon(polygon_coords)
    polygon_wkt = polygon.wkt

    # --- Column Definitions for Rhein_ais_data ---
    # This dictionary now matches your CREATE TABLE statement.
    COLUMN_DEFINITIONS = {
        "id": {"type": "BIGINT", "nullable": False},
        "time_date": {"type": "TIMESTAMP", "nullable": False},
        "msg_type": {"type": "SMALLINT", "nullable": False},
        "repeatid": {"type": "SMALLINT", "nullable": True},
        "mmsi": {"type": "INTEGER", "nullable": False},
        "statusname": {"type": "SMALLINT", "nullable": True},
        "turn": {"type": "INTEGER", "nullable": True},
        "speed": {"type": "DECIMAL(5,1)", "nullable": True},
        "accuracy": {"type": "VARCHAR(20)", "nullable": True},
        "lon": {"type": "DECIMAL(10,6)", "nullable": False},
        "lat": {"type": "DECIMAL(9,6)", "nullable": False},
        "course": {"type": "DECIMAL(5,1)", "nullable": True},
        "heading": {"type": "SMALLINT", "nullable": True},
        "seconds": {"type": "SMALLINT", "nullable": True},
        "maneuver": {"type": "SMALLINT", "nullable": True},
        "raim": {"type": "VARCHAR(20)", "nullable": True},
        "radio": {"type": "INTEGER", "nullable": True},
    }

    SELECT_COLUMNS = list(COLUMN_DEFINITIONS.keys())

    conn = None
    cursor = None

    try:
        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        print("✅ Successfully connected to the database.")

        # Step 1: Retrieve AIS data within the polygon
        print(
            f"\nStep 1: Retrieving AIS data from '{source_table}' within the polygon..."
        )

        query = f"""
        SELECT {', '.join(f'`{col}`' for col in SELECT_COLUMNS)}
        FROM `{source_table}`
        WHERE ST_Within(POINT(lon, lat), ST_GeomFromText('{polygon_wkt}'))
        """

        cursor.execute(query)
        result = cursor.fetchall()

        if not result:
            print("⚠️ No data found within the specified polygon.")
            return

        df = pd.DataFrame(result)
        print(f"✅ Retrieved {len(df)} records from the database.")

        # Step 2: Create the target table if it doesn't exist
        print(f"\nStep 2: Creating/verifying table '{target_table}'...")

        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS `{target_table}` (
            `pk_id` INT AUTO_INCREMENT PRIMARY KEY,
            {', '.join([f"`{col}` {defn['type']} {'NOT NULL' if not defn['nullable'] else 'DEFAULT NULL'}" 
                        for col, defn in COLUMN_DEFINITIONS.items()])}
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

        cursor.execute(create_table_sql)
        conn.commit()
        print(f"✅ Table '{target_table}' is ready.")

        # Step 3: Prepare data for insertion
        print("\nStep 3: Preparing data for insertion...")

        df = df.replace({np.nan: None, pd.NaT: None})

        datetime_cols = ["time_date"]
        for col in datetime_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d %H:%M:%S")

        insert_sql = f"""
        INSERT INTO `{target_table}` ({', '.join([f'`{col}`' for col in SELECT_COLUMNS])})
        VALUES ({', '.join(['%s'] * len(SELECT_COLUMNS))})
        """

        data_to_insert = [
            tuple(row) for row in df[SELECT_COLUMNS].to_records(index=False)
        ]

        # --- Step 4: Insert data in batches ---
        print("\nStep 4: Inserting data in batches...")

        def convert_numpy_types(value):
            """Convert numpy types to native Python types for MySQL compatibility."""
            if pd.isna(value):
                return None
            if isinstance(value, (np.int64, np.int32)):
                return int(value)
            if isinstance(value, (np.float64, np.float32)):
                return float(value)
            return value

        batch_size = 1000
        total_rows = len(data_to_insert)

        for i in range(0, total_rows, batch_size):
            batch = data_to_insert[i : i + batch_size]

            # Convert all numpy types in the batch to standard Python types
            converted_batch = [
                tuple(convert_numpy_types(v) for v in row) for row in batch
            ]

            cursor.executemany(insert_sql, converted_batch)
            conn.commit()
            print(f"Inserted {min(i + batch_size, total_rows)} of {total_rows} rows...")

        print(f"\n✅ Successfully inserted {total_rows} rows into '{target_table}'.")

    except mysql.connector.Error as err:
        print(f"❌ Database error (MySQL Error Code: {err.errno}): {err.msg}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            print("\nMySQL connection closed.")


if __name__ == "__main__":
    get_and_save_ais_data_to_table()
    print("\nProcess completed.")
