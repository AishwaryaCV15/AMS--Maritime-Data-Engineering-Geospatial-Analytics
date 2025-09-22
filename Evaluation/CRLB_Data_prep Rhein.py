import mysql.connector
import numpy as np
import matplotlib.pyplot as plt
from math import radians, sin, cos, sqrt, atan2, degrees
from scipy.ndimage import uniform_filter1d
import pandas as pd


# ---------------------------
# 1. HELPER FUNCTIONS
# ---------------------------
def haversine(lat1, lon1, lat2, lon2):
    """Calculate great circle distance between two points in meters."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return 6371000 * c


def latlon_to_xy(lat, lon, lat_ref, lon_ref):
    """Convert lat/lon to local x,y coordinates in meters."""
    R = 6371000
    x = R * radians(lon - lon_ref) * cos(radians(lat_ref))
    y = R * radians(lat - lat_ref)
    return x, y


def calculate_track_direction(lats, lons):
    """Calculate overall direction (bearing) of a track in degrees."""
    if len(lats) < 2:
        return 0.0
    n = len(lats)
    idx1, idx2 = n // 10, n - (n // 10)
    lat1, lon1 = radians(lats[idx1]), radians(lons[idx1])
    lat2, lon2 = radians(lats[idx2]), radians(lons[idx2])
    dlon = lon2 - lon1
    x = sin(dlon) * cos(lat2)
    y = cos(lat1) * sin(lat2) - (sin(lat1) * cos(lat2) * cos(dlon))
    initial_bearing = atan2(x, y)
    return (degrees(initial_bearing) + 360) % 360


def calculate_distance_to_segment(point, segment_start, segment_end):
    """
    Calculate perpendicular distance from a point to a line segment.
    Returns the distance and the closest point on the segment.
    """
    # Convert to vectors
    point = np.array(point)
    seg_start = np.array(segment_start)
    seg_end = np.array(segment_end)

    # Vector calculations
    seg_vec = seg_end - seg_start
    seg_length = np.linalg.norm(seg_vec)

    if seg_length == 0:  # Segment is a point
        return np.linalg.norm(point - seg_start), seg_start

    # Calculate projection
    t = np.dot(point - seg_start, seg_vec) / (seg_length**2)
    t = max(0, min(1, t))  # Clamp to segment

    # Closest point on segment
    closest_point = seg_start + t * seg_vec
    distance = np.linalg.norm(point - closest_point)

    return distance, closest_point


# ---------------------------
# 2. CORE ANALYSIS FUNCTION
# ---------------------------
def calculate_empirical_lower_bound(lats, lons, window_size=5):
    """
    CORRECTED version: Calculates GPS noise as perpendicular distance to smoothed path.
    Maintains backward compatibility with original function call.
    """
    # Input validation
    if len(lats) != len(lons):
        raise ValueError("Latitude and longitude arrays must have the same length")

    if len(lats) < window_size:
        raise ValueError(
            f"Track too short ({len(lats)} points) for window size {window_size}"
        )

    if window_size % 2 == 0:
        raise ValueError("Window size must be an odd integer")

    # Convert to local coordinates using first point as reference
    lat_ref, lon_ref = lats[0], lons[0]
    x_raw, y_raw = [], []
    for lat, lon in zip(lats, lons):
        x, y = latlon_to_xy(lat, lon, lat_ref, lon_ref)
        x_raw.append(x)
        y_raw.append(y)

    x_raw = np.array(x_raw)
    y_raw = np.array(y_raw)

    # Apply moving average filter to smooth the track
    x_smooth = uniform_filter1d(x_raw, size=window_size, mode="mirror")
    y_smooth = uniform_filter1d(y_raw, size=window_size, mode="mirror")

    # Calculate PERPENDICULAR distance to smoothed path (like XTE)
    deviations = []
    for i in range(len(x_raw)):
        # For each point, find perpendicular distance to smoothed path
        if i == 0:
            # For first point, use distance to first smoothed point
            dist = np.sqrt(
                (x_raw[i] - x_smooth[i]) ** 2 + (y_raw[i] - y_smooth[i]) ** 2
            )
        else:
            # For other points, find perpendicular distance to line segment
            seg_start = (x_smooth[i - 1], y_smooth[i - 1])
            seg_end = (x_smooth[i], y_smooth[i])
            point = (x_raw[i], y_raw[i])
            dist, _ = calculate_distance_to_segment(point, seg_start, seg_end)
        deviations.append(dist)

    deviations = np.array(deviations)
    rms_noise = np.sqrt(np.mean(deviations**2))

    return rms_noise  # Return only the RMS value for compatibility


# ---------------------------
# 3. DATABASE & TRACK MANAGEMENT
# ---------------------------


def load_single_historic_track(mmsi, start_time=None, end_time=None):
    """
    Loads a single historic AIS track for a specific MMSI, optionally within a time window.
    Returns data in both geographic and local Cartesian coordinates.
    """

    db_config = {
        "host": "localhost",
        "user": "root",
        "password": "AMS_ship_traj03",
        "database": "ship_data",
    }

    # Initialize empty arrays to store the data
    times = []
    lats = []
    lons = []
    sogs = []
    headings = []

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # SQL Query to fetch data
        query_cols = (
            "`mmsi`, `latitude`, `longitude`, `sog`, `true_heading`, `recv_time`"
        )
        table_name = "rhein_ais_data_env"

        query = f"""
        SELECT {query_cols}
        FROM `{table_name}`
        WHERE mmsi = %s
        """
        params = [mmsi]

        # Add time window filters if provided
        if start_time and end_time:
            query += " AND `recv_time` BETWEEN %s AND %s"
            params.extend([start_time, end_time])
        elif start_time:
            query += " AND `recv_time` >= %s"
            params.append(start_time)
        elif end_time:
            query += " AND `recv_time` <= %s"
            params.append(end_time)

        query += " ORDER BY `recv_time` ASC;"

        print(f"Executing query for MMSI {mmsi}...")
        cursor.execute(query, params)
        results = cursor.fetchall()

        if not results:
            print(f"No data found for MMSI {mmsi}")
            return None

        # Extract data from results
        for row in results:
            times.append(row["recv_time"])
            lats.append(float(row["latitude"]))  # Convert to float
            lons.append(float(row["longitude"]))  # Convert to float
            sogs.append(float(row["sog"]))
            headings.append(float(row["true_heading"]))

        print(f"Loaded {len(times)} data points for MMSI {mmsi}")

        # Convert to numpy arrays
        times = np.array(times)
        lats = np.array(lats)
        lons = np.array(lons)
        sogs = np.array(sogs)
        headings = np.array(headings)

        # Convert to Local Cartesian Coordinates
        lat_ref = lats[0]
        lon_ref = lons[0]

        x_path, y_path = [], []
        for lat, lon in zip(lats, lons):
            x, y = latlon_to_xy(lat, lon, lat_ref, lon_ref)
            x_path.append(x)
            y_path.append(y)

        x_path = np.array(x_path)
        y_path = np.array(y_path)

        # Calculate cumulative distance along path
        distances = [0.0]
        for i in range(1, len(lats)):
            dist = haversine(lats[i - 1], lons[i - 1], lats[i], lons[i])
            distances.append(distances[-1] + dist)
        distances = np.array(distances)

        return {
            "mmsi": mmsi,
            "times": times,
            "lats": lats,
            "lons": lons,
            "sogs": sogs,
            "headings": headings,
            "x": x_path,
            "y": y_path,
            "distances": distances,
            "ref_point": (lat_ref, lon_ref),
        }

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return None
    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()


def plot_track_comparison(prepared_tracks):
    """
    Plots all prepared tracks in both geographic and local coordinates.
    """
    n_tracks = len(prepared_tracks)
    colors = plt.cm.tab10(np.linspace(0, 1, n_tracks))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Plot 1: Geographic coordinates
    for i, (track_id, track_data) in enumerate(prepared_tracks.items()):
        ax1.plot(
            track_data["lons"],
            track_data["lats"],
            color=colors[i],
            marker="o",
            markersize=2,
            linewidth=1,
            label=f'{track_id} (MMSI: {track_data["mmsi"]})',
        )

    ax1.set_title("Geographic Coordinates - All Tracks")
    ax1.set_xlabel("Longitude")
    ax1.set_ylabel("Latitude")
    ax1.grid(True)
    ax1.legend()

    # Plot 2: Local Cartesian coordinates
    for i, (track_id, track_data) in enumerate(prepared_tracks.items()):
        ax2.plot(
            track_data["x"],
            track_data["y"],
            color=colors[i],
            marker="o",
            markersize=2,
            linewidth=1,
            label=f'{track_id} (MMSI: {track_data["mmsi"]})',
        )

    ax2.set_title("Local Cartesian Coordinates - All Tracks (Meters)")
    ax2.set_xlabel("East (m)")
    ax2.set_ylabel("North (m)")
    ax2.grid(True)
    ax2.axis("equal")
    ax2.legend()

    plt.tight_layout()
    plt.show()


def create_summary_dataframe(prepared_tracks):
    """
    Creates a summary DataFrame with key statistics for all tracks.
    """
    summary_data = []

    for track_id, track_data in prepared_tracks.items():
        summary_data.append(
            {
                "Track_ID": track_id,
                "MMSI": track_data["mmsi"],
                "Num_Points": len(track_data["times"]),
                "Duration_hrs": (
                    track_data["times"][-1] - track_data["times"][0]
                ).total_seconds()
                / 3600,
                "Total_Distance_m": track_data["distances"][-1],
                "Avg_SOG_knots": np.mean(track_data["sogs"]),
                "Lat_Range": f"{track_data['lats'].min():.6f} to {track_data['lats'].max():.6f}",
                "Lon_Range": f"{track_data['lons'].min():.6f} to {track_data['lons'].max():.6f}",
                "X_Range_m": f"{track_data['x'].min():.1f} to {track_data['x'].max():.1f}",
                "Y_Range_m": f"{track_data['y'].min():.1f} to {track_data['y'].max():.1f}",
                "Ref_Point": f"{track_data['ref_point'][0]:.6f}, {track_data['ref_point'][1]:.6f}",
            }
        )

    return pd.DataFrame(summary_data)


# ---------------------------
# 4. MAIN EXECUTION
# ---------------------------
if __name__ == "__main__":
    # Define tracks to load
    tracks_to_load = [
        {
            "mmsi": 244660532,
            "start_time": "2025-03-09 11:49:09",
            "end_time": "2025-03-09 12:22:27",
            "id": "H1",2025-03-09 11:49:09
        },
        {
            "mmsi": 244660361,
            "start_time": "2025-03-09 00:00:20",
            "end_time": "2025-03-09 00:08:31",
            "id": "H2",
        },
        {
            "mmsi": 211729530,
            "start_time": "2025-03-15 12:31:47",
            "end_time": "2025-03-15 12:49:57",
            "id": "H3",
        },
    ]

    prepared_tracks = {}
    direction_groups = {}

    # Load and classify tracks
    for track_info in tracks_to_load:
        track_data = load_single_historic_track(
            mmsi=track_info["mmsi"],
            start_time=track_info["start_time"],
            end_time=track_info["end_time"],
        )

        if track_data is not None:
            # Classify direction
            bearing = calculate_track_direction(track_data["lats"], track_data["lons"])
            group_name = "Northbound" if bearing < 180 else "Southbound"
            track_data["direction_group"] = group_name
            track_data["bearing"] = bearing

            prepared_tracks[track_info["id"]] = track_data

            if group_name not in direction_groups:
                direction_groups[group_name] = []
            direction_groups[group_name].append(track_info["id"])

    # Calculate CRLB for each direction group
    print("\n--- Empirical Lower Bound (CRLB) Calculation ---")
    crlb_results = {}

    for group_name, track_ids in direction_groups.items():
        print(f"\n{group_name} Tracks: {track_ids}")
        group_crlbs = []

        for track_id in track_ids:
            track_data = prepared_tracks[track_id]
            try:
                crlb = calculate_empirical_lower_bound(
                    track_data["lats"], track_data["lons"]
                )
                print(f"CRLB for this track: {crlb:.2f} m")
                group_crlbs.append(crlb)
                print(
                    f"  {track_id}: CRLB = {crlb:.3f} m (Bearing: {track_data['bearing']:.1f}°)"
                )
            except ValueError as e:
                print(f"  {track_id}: Error - {e}")

        if group_crlbs:
            avg_crlb = np.mean(group_crlbs)
            crlb_results[group_name] = avg_crlb
            print(f"  Average {group_name} CRLB: {avg_crlb:.3f} m")

    print("\nFinal Results:")
    for group, crlb in crlb_results.items():
        print(f"  {group}: {crlb:.3f} m")

    # 4. Plot all tracks in local coordinates
    if prepared_tracks:
        print("\nGenerating comparison plots...")
        plot_track_comparison(prepared_tracks)

        # 5. Create summary statistics
        print("\nGenerating summary statistics...")
        summary_df = create_summary_dataframe(prepared_tracks)
        print("\nSummary of Prepared Tracks:")
        print(summary_df.to_string(index=False))

        # 6. (Optional) Save the prepared tracks to file for later use
        print("\nSaving prepared tracks to file...")
        np.savez("prepared_historic_tracksR.npz", **prepared_tracks)
        print("Tracks saved to 'prepared_historic_tracksR.npz'")

        # Save summary to CSV
        summary_df.to_csv("track_summaryR.csv", index=False)
        print("Summary saved to 'track_summaryR.csv'")

        # Display detailed info for each track
        for track_id, track_data in prepared_tracks.items():
            print(f"\nDetailed info for {track_id}:")
            print(f"  MMSI: {track_data['mmsi']}")
            print(f"  Points: {len(track_data['times'])}")
            print(f"  Duration: {(track_data['times'][-1] - track_data['times'][0])}")
            print(f"  Total distance: {track_data['distances'][-1]:.2f} meters")
            print(f"  Average SOG: {np.mean(track_data['sogs']):.2f} knots")
            print(f"  Reference point: {track_data['ref_point']}")
    else:
        print("No tracks were successfully loaded.")
