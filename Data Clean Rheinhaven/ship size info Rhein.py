import csv


def extract_vessel_dimensions_with_details(input_file, output_file):
    """
    Reads vessel tracking data from a CSV file, processes it to calculate
    dimensions and categorize vessels, and writes a summary to a new CSV file.

    Args:
        input_file (str): The path to the input CSV file.
        output_file (str): The path where the output summary CSV will be saved.
    """
    vessel_info = (
        {}
    )  # Use a dictionary to store the first valid entry for each vessel, keyed by MMSI.

    with open(input_file, "r", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        for row_num, row in enumerate(reader, 1):
            # Skip empty rows
            if not row:
                continue

            try:
                # Use 'mmsi' as the unique identifier for the vessel.
                user_id = row.get("mmsi")
                if not user_id:
                    continue

                # Process each vessel only once, taking its first appearance in the file.
                if user_id not in vessel_info:
                    # Extract and convert dimension data to integers.
                    # 'to_bow' corresponds to Dimension A
                    dim_a = int(row.get("to_bow", 0)) if row.get("to_bow") else 0
                    # 'to_stern' corresponds to Dimension B
                    dim_b = int(row.get("to_stern", 0)) if row.get("to_stern") else 0
                    # 'to_port' corresponds to Dimension C
                    dim_c = int(row.get("to_port", 0)) if row.get("to_port") else 0
                    # 'to_starboard' corresponds to Dimension D
                    dim_d = (
                        int(row.get("to_starboard", 0))
                        if row.get("to_starboard")
                        else 0
                    )

                    # Combine ETA components into a formatted string.
                    # Handle potential errors if date/time parts are missing or invalid.
                    try:
                        eta_month = int(row.get("month_info", 0))
                        eta_day = int(row.get("day_info", 0))
                        eta_hour = int(row.get("hour_info", 0))
                        eta_minute = int(row.get("minute_info", 0))
                        # Create a datetime object assuming the current year if not specified
                        # Note: This might not be accurate for data spanning multiple years.
                        if all([eta_month, eta_day]):
                            eta_str = f"{eta_day:02d}-{eta_month:02d} {eta_hour:02d}:{eta_minute:02d}"
                        else:
                            eta_str = "Unknown"
                    except (ValueError, TypeError):
                        eta_str = "Invalid ETA"

                    # Store the vessel's information if it has valid dimensions.
                    if any([dim_a, dim_b, dim_c, dim_d]):
                        vessel_info[user_id] = {
                            "Name": row.get("shipname", "Unknown"),
                            "Destination": row.get("destination", "Unknown"),
                            "ETA": eta_str,
                            "Max Draught": row.get("draught", "Unknown"),
                            "Ship Type": row.get("ship_type", "Unknown"),
                            "IMO Number": row.get("imo", "Unknown"),
                            "Call Sign": row.get("callsign", "Unknown"),
                            "Dimension A": dim_a,
                            "Dimension B": dim_b,
                            "Dimension C": dim_c,
                            "Dimension D": dim_d,
                        }

            except Exception as e:
                print(f"⚠️ Error processing row {row_num}: {e}")
                continue

    # Prepare data for the summary CSV file.
    summary_rows = []
    for user_id, entry in vessel_info.items():
        # Calculate total length and width (beam).
        length = entry.get("Dimension A", 0) + entry.get("Dimension B", 0)
        width = entry.get("Dimension C", 0) + entry.get("Dimension D", 0)

        # Categorize the vessel based on its beam.
        if width < 10:
            beam_category = "Beam < 10m"
        elif 10 <= width < 23:
            beam_category = "10m ≤ Beam < 23m"
        elif 23 <= width < 33:
            beam_category = "23m ≤ Beam < 33m"
        else:
            beam_category = "Beam ≥ 33m"

        summary_rows.append(
            {
                "MMSI": user_id,
                "Name": entry.get("Name", "Unknown"),
                "Destination": entry.get("Destination", "Unknown"),
                "ETA": entry.get("ETA", "Unknown"),
                "Max Draught": entry.get("Max Draught", "Unknown"),
                "Ship Type": entry.get("Ship Type", "Unknown"),
                "IMO Number": entry.get("IMO Number", "Unknown"),
                "Call Sign": entry.get("Call Sign", "Unknown"),
                "Length (m)": length,
                "Beam (m)": width,
                "Beam Category": beam_category,
                "Dimension A": entry.get("Dimension A", 0),
                "Dimension B": entry.get("Dimension B", 0),
                "Dimension C": entry.get("Dimension C", 0),
                "Dimension D": entry.get("Dimension D", 0),
            }
        )

    # Define the fieldnames for the output CSV file.
    fieldnames = [
        "MMSI",
        "Name",
        "Destination",
        "ETA",
        "Max Draught",
        "Ship Type",
        "IMO Number",
        "Call Sign",
        "Length (m)",
        "Beam (m)",
        "Beam Category",
        "Dimension A",
        "Dimension B",
        "Dimension C",
        "Dimension D",
    ]

    # Write the processed data to the output CSV file.
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"✅ Saved vessel summary for {len(summary_rows)} vessels to {output_file}")


if __name__ == "__main__":
    # --- IMPORTANT ---
    # Update this path to the actual location of your input CSV file.
    input_file = "C:/Users/cvais/Documents/GitHub/AMS_ShipTraj/split_output/static_voyage_data.csv"
    output_file = "vessel_details_summary_R.csv"
    extract_vessel_dimensions_with_details(input_file, output_file)
