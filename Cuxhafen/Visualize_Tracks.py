import mysql.connector
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from mysql.connector import errorcode
import json


def fetch_ais_data_from_db(db_config, mmsi=None):
    """
    Fetches AIS data from the database, specifically for plotting trajectories.
    Orders data by 'recv_time'.

    Args:
        db_config (dict): Dictionary containing database connection details.
        mmsi (int, optional): The specific MMSI to fetch data for.
                              If None, fetches data for all MMSIs (use with caution for large datasets).

    Returns:
        pandas.DataFrame: A DataFrame containing the fetched AIS data,
                          with columns renamed to match plotting functions.
    """
    conn = None
    cursor = None
    ais_data = pd.DataFrame()  # Initialize an empty DataFrame

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)  # Fetch results as dictionaries

        # --- SQL Query to fetch data ---
        # Adjusted column names to exactly match the provided database schema (lowercase)
        # 'recv_time' is crucial for ordering the trajectory.
        query_cols = "`mmsi`, `latitude`, `longitude`, `sog`, `true_heading`, `recv_time` ,`datetime_utc`"
        table_name = "rhein_ais_data_env"

        query = f"""
        SELECT {query_cols}
        FROM `{table_name}`
        """
        params = []

        if mmsi is not None:
            query += " WHERE mmsi = %s  and recv_time between '2025-03-09 11:49:09' and '2025-03-09 12:22:27' "  # and datetime_utc between '2025-04-27 06:59:17' and  '2025-04-27 07:32:19'"  # and datetime_utc between '2025-04-20 01:07:37' and '2025-04-20 01:12:17'"
            params.append(mmsi)

        query += " ORDER BY `recv_time` ASC;"

        print(f"Executing query: {query.strip()}")
        cursor.execute(query, tuple(params) if params else None)

        data = cursor.fetchall()
        if data:
            ais_data = pd.DataFrame(data)
            print(f"Fetched {len(ais_data)} rows from '{table_name}'.")

            # Rename columns to match the existing plotting functions
            # Ensure these map correctly from DB names (lowercase) to function expected names
            ais_data = ais_data.rename(
                columns={
                    "mmsi": "User ID",
                    "recv_time": "Time stamp",
                    "datetime_utc": "Time stamp1",
                    "latitude": "Latitude",  # Explicitly map for clarity
                    "longitude": "Longitude",  # Explicitly map for clarity
                    "sog": "SOG",  # Explicitly map for clarity
                    "true_heading": "True heading",  # Map to the expected 'True heading'
                }
            )
            # Convert 'Time stamp' (which was 'recv_time') to datetime objects
            ais_data["Time stamp"] = pd.to_datetime(
                ais_data["Time stamp"], unit="s"
            )  # Assuming recv_time is Unix timestamp in seconds
            print("Columns renamed and 'Time stamp' converted to datetime.")
        else:
            print(
                f"No data found in '{table_name}' for MMSI {mmsi if mmsi else 'all'} or table is empty."
            )

    except mysql.connector.Error as err:
        print(f"Database error (MySQL Error Code: {err.errno}): {err.msg}")
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("  Hint: Check your database username or password.")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("  Hint: The specified database does not exist.")
        elif err.errno == errorcode.ER_NO_SUCH_TABLE:
            print(
                f"  Hint: Table '{table_name}' does not exist in your database. Please ensure the table name is correct."
            )
        elif err.errno == 2003:
            print(
                "  Hint: Cannot connect to MySQL server. Ensure MySQL is running and host/port are correct."
            )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            print("MySQL connection closed.")
    return ais_data


def calculate_total_duration(df):
    """
    Calculates the total duration for each vessel (User ID) based on 'Time stamp'.

    Args:
        df (pandas.DataFrame): DataFrame with 'User ID' and 'Time stamp' columns.

    Returns:
        pandas.DataFrame: Original DataFrame with a 'total_duration' column added.
    """
    if "Time stamp" not in df.columns or "User ID" not in df.columns:
        print(
            "Error: DataFrame must contain 'Time stamp' and 'User ID' columns for duration calculation."
        )
        return df  # Return original df if essential columns are missing

    # Ensure 'Time stamp' is datetime
    df["Time stamp"] = pd.to_datetime(df["Time stamp"])

    # Group by User ID to calculate duration per vessel
    # .transform ensures the result is broadcast back to the original DataFrame's shape
    df["total_duration"] = df.groupby("User ID")["Time stamp"].transform(
        lambda x: x.max() - x.min() if not x.empty else pd.Timedelta(seconds=0)
    )
    return df


def plot_vessel_trajectory(df, user_id):
    """
    Plots the trajectory of a specific vessel on a Folium map.

    Args:
        df (pandas.DataFrame): DataFrame containing AIS data, including
                               'Latitude', 'Longitude', 'User ID', 'Time stamp',
                               'SOG', 'True heading', and 'total_duration'.
        user_id (int): The User ID (MMSI) of the vessel to plot.

    Returns:
        folium.Map: A Folium map object with the vessel's trajectory and markers.
    """
    # Filter the dataset for the given user_id and sort by timestamp
    vessel_data = (
        df[df["User ID"] == user_id].sort_values(by="Time stamp").reset_index(drop=True)
    )

    if vessel_data.empty:
        print(f"No data available for User ID: {user_id}. Cannot plot trajectory.")
        # Return a default empty map if no data for the specific vessel
        return folium.Map(location=[0, 0], zoom_start=2)

    # Calculate total duration for this specific vessel (already done in main, but ensuring here)
    # Ensure 'total_duration' is available for the current vessel
    total_duration_str = "N/A"
    if "total_duration" in vessel_data.columns and not vessel_data.empty:
        # Get the first duration value for this user_id, as it's constant for all rows of that ID
        duration_series = vessel_data["total_duration"].drop_duplicates()
        if not duration_series.empty:
            total_duration_str = str(duration_series.iloc[0])

    # Get the starting and ending points of the vessel
    # Use .iloc[0] and .iloc[-1] after sorting to get actual start/end points
    start_lat = vessel_data["Latitude"].iloc[0]
    start_lon = vessel_data["Longitude"].iloc[0]
    end_lat = vessel_data["Latitude"].iloc[-1]
    end_lon = vessel_data["Longitude"].iloc[-1]

    # Create a folium map centered at the starting point
    folium_map = folium.Map(location=[start_lat, start_lon], zoom_start=12)

    # Create a MarkerCluster to group markers for start and end points
    marker_cluster = MarkerCluster().add_to(folium_map)

    # Add a marker for the starting point with information
    folium.Marker(
        location=[start_lat, start_lon],
        popup=f"<b>Start Point</b><br>"
        f"Time: {vessel_data['Time stamp'].iloc[0]}<br>"
        f"Time2: {vessel_data['Time stamp1'].iloc[0]}<br>"
        f"Speed: {vessel_data['SOG'].iloc[0]} knots<br>"
        f"Course: {vessel_data['True heading'].iloc[0]}°",
        icon=folium.Icon(
            color="green", icon="play", prefix="fa"
        ),  # Using Font Awesome icons
    ).add_to(marker_cluster)

    # Add a marker for the ending point with information
    folium.Marker(
        location=[end_lat, end_lon],
        popup=f"<b>End Point</b><br>"
        f"Time: {vessel_data['Time stamp'].iloc[-1]}<br>"
        f"Speed: {vessel_data['SOG'].iloc[-1]} knots<br>"
        f"Course: {vessel_data['True heading'].iloc[-1]}°<br>"
        f"Total Duration: {total_duration_str}",
        icon=folium.Icon(
            color="red", icon="stop", prefix="fa"
        ),  # Using Font Awesome icons
    ).add_to(marker_cluster)

    # Plot the trajectory of the ship
    # Use only Latitude and Longitude for locations
    route = folium.PolyLine(
        locations=list(zip(vessel_data["Latitude"], vessel_data["Longitude"])),
        color="blue",
        weight=2.5,
        opacity=1,
    ).add_to(folium_map)

    # Add a popup with route details
    folium.Popup(f"Ship's route for User ID: {user_id}", max_width=200).add_to(route)

    # Add optional CircleMarkers for each point (can be slow for many points)
    for idx, row in vessel_data.iterrows():
        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=3,
            color="purple",
            fill=True,
            fill_color="purple",
            fill_opacity=0.6,
            popup=f"Time: {row['Time stamp']}<br>UTC:{row['Time stamp1']}<br>SOG: {row['SOG']}<br>COG: {row['True heading']}",
        ).add_to(folium_map)

    return folium_map


def add_static_lines_from_json_files(json_files, folium_map):
    all_points = []  # collect coords for fit_bounds

    for json_file in json_files:
        try:
            with open(json_file, "r") as f:
                data = json.load(f)

            # Case A: reference_trajectory (dict of dicts with lat/lon)
            if isinstance(data, dict) and all(
                isinstance(v, dict) for v in data.values()
            ):
                coords = [(v["latitude"], v["longitude"]) for v in data.values()]
                folium.PolyLine(
                    locations=coords,
                    color="black",
                    weight=3,
                    opacity=0.8,
                    popup=f"Reference Trajectory ({json_file})",
                ).add_to(folium_map)
                all_points.extend(coords)

            # Case B: line_of_sight (list of [lat, lon])
            elif isinstance(data, list) and all(isinstance(pt, list) for pt in data):
                folium.PolyLine(
                    locations=data,
                    color="orange",
                    weight=3,
                    dash_array="5, 5",
                    popup=f"Line of Sight ({json_file})",
                ).add_to(folium_map)
                all_points.extend(data)

            # Case C: portlines (dict with multiple lists of coords)
            elif isinstance(data, dict) and all(
                isinstance(v, list) for v in data.values()
            ):
                for name, coords in data.items():
                    folium.PolyLine(
                        locations=coords,
                        color="red",
                        weight=2,
                        opacity=0.7,
                        popup=f"{name} ({json_file})",
                    ).add_to(folium_map)
                    all_points.extend(coords)

            else:
                print(f"Unrecognized format in {json_file}, skipping.")

            print(f"Static line(s) added from {json_file}.")

        except Exception as e:
            print(f"Error adding static line from {json_file}: {e}")

    # Auto-fit map to show everything
    if all_points:
        folium_map.fit_bounds(all_points)


if __name__ == "__main__":
    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "AMS_ship_traj03",
        "database": "ship_data",
    }

    target_mmsi = 244660532

    print("Starting data retrieval and plotting process...")
    ais_data_for_plot = fetch_ais_data_from_db(db_config, mmsi=target_mmsi)

    if not ais_data_for_plot.empty:
        ais_data_for_plot = calculate_total_duration(ais_data_for_plot)
        print("Total durations calculated.")

        print(f"Generating map for MMSI: {target_mmsi}...")
        folium_map = plot_vessel_trajectory(ais_data_for_plot, target_mmsi)

        # Add static lines from your two JSON files
        json_files = [
            "log_data S1 R Port.json",
            "Rheinhafen_line_of_sight",
            "portlines.json",
        ]
        add_static_lines_from_json_files(json_files, folium_map)

        # Save the final combined map
        map_filename = "mmsi_encounter_with_static_lines.html"
        folium_map.save(map_filename)
        print(f"Map with AIS + JSON lines saved as '{map_filename}'.")
    else:
        print("No data available to plot trajectory.")
