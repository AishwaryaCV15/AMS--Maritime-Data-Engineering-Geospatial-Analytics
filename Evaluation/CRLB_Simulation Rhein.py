import numpy as np
import pandas as pd
import json
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
from math import radians, sin, cos, sqrt, atan2
import folium
from folium import plugins
from shapely.geometry import LineString, Point


# Load the helper functions (make sure these are defined)
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


def interpolate_to_common_points(
    hist_lats, hist_lons, sim_lats, sim_lons, n_points=1000
):
    """Interpolates both tracks to the same number of points for fair comparison."""
    # Clean data first - remove duplicates
    hist_lats, hist_lons = remove_duplicate_points(hist_lats, hist_lons)
    sim_lats, sim_lons = remove_duplicate_points(sim_lats, sim_lons)

    # Calculate cumulative distance for historic track
    hist_distances = [0.0]
    for i in range(1, len(hist_lats)):
        dist = haversine(hist_lats[i - 1], hist_lons[i - 1], hist_lats[i], hist_lons[i])
        hist_distances.append(hist_distances[-1] + dist)
    hist_distances = np.array(hist_distances)
    hist_distances_norm = hist_distances / hist_distances[-1]

    # Calculate cumulative distance for simulated track
    sim_distances = [0.0]
    for i in range(1, len(sim_lats)):
        dist = haversine(sim_lats[i - 1], sim_lons[i - 1], sim_lats[i], sim_lons[i])
        sim_distances.append(sim_distances[-1] + dist)
    sim_distances = np.array(sim_distances)
    sim_distances_norm = sim_distances / sim_distances[-1]

    # Create common distance array
    common_fraction = np.linspace(0, 1, n_points)

    # Interpolate both tracks
    f_hist_lat = interp1d(
        hist_distances_norm,
        hist_lats,
        kind="linear",
        bounds_error=False,
        fill_value="extrapolate",
    )
    f_hist_lon = interp1d(
        hist_distances_norm,
        hist_lons,
        kind="linear",
        bounds_error=False,
        fill_value="extrapolate",
    )
    hist_lats_i = f_hist_lat(common_fraction)
    hist_lons_i = f_hist_lon(common_fraction)

    f_sim_lat = interp1d(
        sim_distances_norm,
        sim_lats,
        kind="linear",
        bounds_error=False,
        fill_value="extrapolate",
    )
    f_sim_lon = interp1d(
        sim_distances_norm,
        sim_lons,
        kind="linear",
        bounds_error=False,
        fill_value="extrapolate",
    )
    sim_lats_i = f_sim_lat(common_fraction)
    sim_lons_i = f_sim_lon(common_fraction)

    return hist_lats_i, hist_lons_i, sim_lats_i, sim_lons_i, common_fraction


def calculate_rmse_between_paths(hist_lats, hist_lons, sim_lats, sim_lons):
    """Calculates RMSE between historic and simulated paths."""
    hist_lats_i, hist_lons_i, sim_lats_i, sim_lons_i, _ = interpolate_to_common_points(
        hist_lats, hist_lons, sim_lats, sim_lons
    )

    errors = []
    for i in range(len(hist_lats_i)):
        dist = haversine(hist_lats_i[i], hist_lons_i[i], sim_lats_i[i], sim_lons_i[i])
        errors.append(dist)

    errors = np.array(errors)
    rmse = np.sqrt(np.mean(errors**2))
    max_error = np.max(errors)
    mean_error = np.mean(errors)

    return rmse, max_error, mean_error, errors


def remove_duplicate_points(lats, lons, tolerance=1e-10):
    """
    Remove duplicate or very close points that cause interpolation issues.
    tolerance: points closer than this distance (in degrees) are considered duplicates
    """
    if len(lats) == 0:
        return lats, lons

    # Convert to numpy arrays
    lats = np.array(lats)
    lons = np.array(lons)

    # Find unique points
    unique_indices = [0]  # Always keep first point
    for i in range(1, len(lats)):
        # Check distance to previous point
        dist = haversine(lats[i], lons[i], lats[i - 1], lons[i - 1])
        if dist > tolerance:  # Only keep if significantly different
            unique_indices.append(i)

    return lats[unique_indices], lons[unique_indices]


def load_simulation_from_json(file_path):
    """Loads simulation data from JSON file."""
    try:
        with open(file_path, "r") as f:
            sim_data = json.load(f)

        # Convert to list of points and sort by timestamp
        points = []
        for key, point_data in sim_data.items():
            try:
                points.append(
                    {
                        "timestamp": float(point_data["timestamp"]),
                        "lat": float(point_data["latitude"]),
                        "lon": float(point_data["longitude"]),
                        "x_vel": float(point_data.get("x_velocity", 0)),
                        "y_vel": float(point_data.get("y_velocity", 0)),
                        "heading": float(point_data.get("heading", 0)),
                    }
                )
            except (ValueError, KeyError) as e:
                print(f"Warning: Skipping point {key} due to error: {e}")
                continue

        # Sort by timestamp
        points.sort(key=lambda x: x["timestamp"])

        # Extract sorted latitudes and longitudes
        lats = [point["lat"] for point in points]
        lons = [point["lon"] for point in points]

        return {
            "lats": np.array(lats),
            "lons": np.array(lons),
            "timestamps": np.array([point["timestamp"] for point in points]),
            "data": points,
        }

    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def compute_simulation_rmse(prepared_tracks, simulation_files):
    """Computes RMSE for simulation files against historic tracks."""
    results = {}

    print("Loading simulation data...")

    # Load all simulation data
    simulation_data = {}
    for sim_id, file_path in simulation_files.items():
        print(f"Loading {sim_id} from {file_path}...")
        sim_data = load_simulation_from_json(file_path)
        if sim_data is not None:
            simulation_data[sim_id] = sim_data
            print(f"  Loaded {len(sim_data['lats'])} points")
        else:
            print(f"  Failed to load {sim_id}")

    # Compute RMSE for each combination
    for hist_track_id, hist_data in prepared_tracks.items():
        results[hist_track_id] = {}
        hist_direction = hist_data.get("direction_group", "Unknown")

        print(f"\nComparing against historic track {hist_track_id} ({hist_direction}):")

        for sim_id, sim_data in simulation_data.items():
            try:
                rmse, max_error, mean_error, errors = calculate_rmse_between_paths(
                    hist_data["lats"],
                    hist_data["lons"],
                    sim_data["lats"],
                    sim_data["lons"],
                )

                results[hist_track_id][sim_id] = {
                    "rmse": rmse,
                    "max_error": max_error,
                    "mean_error": mean_error,
                    "direction_match": hist_direction,
                }

                print(f"  {sim_id}: RMSE = {rmse:.3f} m, Max = {max_error:.3f} m")

            except Exception as e:
                print(f"  Error comparing {sim_id} with {hist_track_id}: {e}")
                results[hist_track_id][sim_id] = None

    return results, simulation_data


def calculate_true_lateral_offset(hist_lats, hist_lons, sim_lats, sim_lons):
    """
    Calculate true lateral offset by finding corresponding points.
    """
    # Interpolate both tracks to common points
    hist_lats_i, hist_lons_i, sim_lats_i, sim_lons_i, _ = interpolate_to_common_points(
        hist_lats, hist_lons, sim_lats, sim_lons
    )

    offsets = []
    for i in range(len(hist_lats_i)):
        # Now points correspond to the same position along the path
        dist = haversine(hist_lats_i[i], hist_lons_i[i], sim_lats_i[i], sim_lons_i[i])
        offsets.append(dist)

    return np.mean(offsets)


def debug_rmse_calculation_specific(hist_lats, hist_lons, sim_lats, sim_lons):
    """
    Debug why RMSE is large when points are actually close.
    """
    print("=== RM CALCULATION DEBUGGING ===")

    # 1. Check if arrays are aligned correctly
    print(f"Historic points: {len(hist_lats)}")
    print(f"Simulation points: {len(sim_lats)}")

    # 2. Check first few points
    print("\nFirst 5 points comparison:")
    for i in range(min(5, len(hist_lats), len(sim_lats))):
        dist = haversine(hist_lats[i], hist_lons[i], sim_lats[i], sim_lons[i])
        print(f"Point {i}:")
        print(f"  Historic:  {hist_lats[i]:.10f}, {hist_lons[i]:.10f}")
        print(f"  Simulation: {sim_lats[i]:.10f}, {sim_lons[i]:.10f}")
        print(f"  Distance:   {dist:.6f} meters")
        print()

    # 3. Check if arrays are in correct order
    print("Checking array order...")
    print(
        f"Historic lat direction: {'increasing' if hist_lats[-1] > hist_lats[0] else 'decreasing'}"
    )
    print(
        f"Simulation lat direction: {'increasing' if sim_lats[-1] > sim_lats[0] else 'decreasing'}"
    )
    print(
        f"Historic lon direction: {'increasing' if hist_lons[-1] > hist_lons[0] else 'decreasing'}"
    )
    print(
        f"Simulation lon direction: {'increasing' if sim_lons[-1] > sim_lons[0] else 'decreasing'}"
    )

    # 4. Check for outliers
    distances = []
    for i in range(min(len(hist_lats), len(sim_lats))):
        dist = haversine(hist_lats[i], hist_lons[i], sim_lats[i], sim_lons[i])
        distances.append(dist)

    distances = np.array(distances)
    print(f"\nDistance statistics:")
    print(f"  Mean distance: {np.mean(distances):.6f} m")
    print(f"  Max distance:  {np.max(distances):.6f} m")
    print(f"  Min distance:  {np.min(distances):.6f} m")
    print(f"  Std dev:       {np.std(distances):.6f} m")

    # 5. Find the problematic points
    if np.max(distances) > 100:  # If any point is >100m away
        outlier_indices = np.where(distances > 100)[0]
        print(f"\nFound {len(outlier_indices)} outlier points (>100m):")
        for idx in outlier_indices[:5]:  # Show first 5 outliers
            print(f"Point {idx}:")
            print(f"  Historic:  {hist_lats[idx]:.10f}, {hist_lons[idx]:.10f}")
            print(f"  Simulation: {sim_lats[idx]:.10f}, {sim_lons[idx]:.10f}")
            print(f"  Distance:   {distances[idx]:.2f} meters")
            print()

            # Create map centered between the two tracks
        center_lat = (hist_lats[0] + sim_lats[0]) / 2
        center_lon = (hist_lons[0] + sim_lons[0]) / 2

        m = folium.Map(location=[center_lat, center_lon], zoom_start=15)  # ZOOM IN!

        # Add historic track
        folium.PolyLine(
            list(zip(hist_lats, hist_lons)),
            color="blue",
            weight=4,
            opacity=0.8,
            tooltip="Historic Track",
        ).add_to(m)

        # Add simulation track
        folium.PolyLine(
            list(zip(sim_lats, sim_lons)),
            color="red",
            weight=4,
            opacity=0.8,
            tooltip="Simulation Track",
        ).add_to(m)

        # Add start points with markers
        folium.Marker(
            [hist_lats[0], hist_lons[0]],
            popup="Historic Start",
            icon=folium.Icon(color="blue"),
        ).add_to(m)

        folium.Marker(
            [sim_lats[0], sim_lons[0]],
            popup="Simulation Start",
            icon=folium.Icon(color="red"),
        ).add_to(m)

        # Add scale bar to see actual distance - CORRECTED
        plugins.MeasureControl().add_to(m)

        m.save("true_scale_comparison.html")
        print("Open true_scale_comparison.html and ZOOM IN to see the actual distance!")


def calculate_path_similarity(hist_lats, hist_lons, sim_lats, sim_lons):
    """
    Calculate path similarity index (0-1, where 1 is perfect match).
    """
    # Interpolate to common points
    hist_lats_i, hist_lons_i, sim_lats_i, sim_lons_i, _ = interpolate_to_common_points(
        hist_lats, hist_lons, sim_lats, sim_lons
    )

    # Calculate correlation of derivatives (shape similarity)
    hist_dlats = np.diff(hist_lats_i)
    hist_dlons = np.diff(hist_lons_i)
    sim_dlats = np.diff(sim_lats_i)
    sim_dlons = np.diff(sim_lons_i)

    # Correlation of direction changes
    corr_dlat = np.corrcoef(hist_dlats, sim_dlats)[0, 1]
    corr_dlon = np.corrcoef(hist_dlons, sim_dlons)[0, 1]

    similarity = (corr_dlat + corr_dlon) / 2
    return max(0, similarity)  # Clip at 0


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


def calculate_cross_track_error_with_points(hist_lats, hist_lons, sim_lats, sim_lons):
    """
    Calculate cross-track error with closest points.
    Returns both xte_errors and closest_points.
    """
    # Convert to local Cartesian coordinates (meters)
    lat_ref, lon_ref = hist_lats[0], hist_lons[0]

    hist_x, hist_y = [], []
    for lat, lon in zip(hist_lats, hist_lons):
        x, y = latlon_to_xy(lat, lon, lat_ref, lon_ref)
        hist_x.append(x)
        hist_y.append(y)

    sim_x, sim_y = [], []
    for lat, lon in zip(sim_lats, sim_lons):
        x, y = latlon_to_xy(lat, lon, lat_ref, lon_ref)
        sim_x.append(x)
        sim_y.append(y)

    # Create historic path segments
    hist_segments = []
    for i in range(len(hist_x) - 1):
        hist_segments.append(((hist_x[i], hist_y[i]), (hist_x[i + 1], hist_y[i + 1])))

    xte_errors = []
    closest_points = []

    # For each simulation point, find distance to closest historic segment
    for sim_point in zip(sim_x, sim_y):
        min_distance = float("inf")
        best_closest_point = None

        for segment in hist_segments:
            seg_start, seg_end = segment
            distance, closest_point = calculate_distance_to_segment(
                sim_point, seg_start, seg_end
            )

            if distance < min_distance:
                min_distance = distance
                best_closest_point = closest_point

        xte_errors.append(min_distance)
        closest_points.append(best_closest_point)

    return np.array(xte_errors), closest_points


def analyze_path_following_performance(hist_lats, hist_lons, sim_lats, sim_lons):
    """
    Complete path following performance analysis.
    """
    print("=== PATH FOLLOWING PERFORMANCE ANALYSIS ===")

    # 1. Calculate Cross-Track Error
    xte_errors, closest_points = calculate_cross_track_error_with_points(
        hist_lats, hist_lons, sim_lats, sim_lons
    )

    print("Cross-Track Error (XTE) Statistics:")
    print(f"  Number of XTE points: {len(xte_errors)}")
    print(f"  Historic points: {len(hist_lats)}")
    print(f"  Simulation points: {len(sim_lats)}")
    print(f"  Mean XTE: {np.mean(xte_errors):.2f} m")
    print(f"  Median XTE: {np.median(xte_errors):.2f} m")
    print(f"  Max XTE: {np.max(xte_errors):.2f} m")
    print(f"  Std XTE: {np.std(xte_errors):.2f} m")
    print(f"  95th percentile XTE: {np.percentile(xte_errors, 95):.2f} m")
    print(f"  99th percentile XTE: {np.percentile(xte_errors, 99):.2f} m")

    # 2. Calculate Path Similarity (if you have this function)
    try:
        similarity = calculate_path_similarity(hist_lats, hist_lons, sim_lats, sim_lons)
        print(f"\nPath Similarity Index: {similarity:.3f}/1.0")
    except:
        print("\nPath Similarity: (function not available)")
        similarity = None

    # 3. Performance Assessment
    mean_xte = np.mean(xte_errors)
    print(f"\nPERFORMANCE ASSESSMENT:")

    if mean_xte < 10:
        assessment = "✅ EXCELLENT: Professional-grade path following"
    elif mean_xte < 20:
        assessment = "✅ VERY GOOD: Excellent path following with minor offsets"
    elif mean_xte < 50:
        assessment = "⚠️  GOOD: Good path following, some tuning needed"
    elif mean_xte < 100:
        assessment = "⚠️  FAIR: Basic path following, needs improvement"
    else:
        assessment = "❌ POOR: Significant path following issues"

    print(assessment)

    # 4. Plot results
    plot_cross_track_analysis(
        hist_lats, hist_lons, sim_lats, sim_lons, xte_errors, closest_points
    )

    return {
        "mean_xte": np.mean(xte_errors),
        "max_xte": np.max(xte_errors),
        "std_xte": np.std(xte_errors),
        "xte_95th": np.percentile(xte_errors, 95),
        "similarity": similarity,
        "n_points": len(xte_errors),
    }


def plot_cross_track_analysis(
    hist_lats, hist_lons, sim_lats, sim_lons, xte_errors, closest_points
):
    """
    Plot the cross-track error analysis.
    """
    # Convert to local coordinates
    lat_ref, lon_ref = hist_lats[0], hist_lons[0]

    hist_x, hist_y = [], []
    for lat, lon in zip(hist_lats, hist_lons):
        x, y = latlon_to_xy(lat, lon, lat_ref, lon_ref)
        hist_x.append(x)
        hist_y.append(y)

    sim_x, sim_y = [], []
    for lat, lon in zip(sim_lats, sim_lons):
        x, y = latlon_to_xy(lat, lon, lat_ref, lon_ref)
        sim_x.append(x)
        sim_y.append(y)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    # Plot 1: Paths with cross-track lines
    ax1.plot(hist_x, hist_y, "b-", label="Historic Path", linewidth=2, alpha=0.7)
    ax1.plot(sim_x, sim_y, "r--", label="Simulation Path", linewidth=2, alpha=0.7)

    # Draw cross-track lines for some points (sample every 5% of simulation points)
    sample_indices = range(0, len(sim_x), max(1, len(sim_x) // 20))
    for i in sample_indices:
        if i < len(closest_points) and closest_points[i] is not None:
            ax1.plot(
                [sim_x[i], closest_points[i][0]],
                [sim_y[i], closest_points[i][1]],
                "g-",
                alpha=0.5,
                linewidth=1,
            )

    ax1.set_xlabel("East (m)")
    ax1.set_ylabel("North (m)")
    ax1.legend()
    ax1.grid(True)
    ax1.axis("equal")
    ax1.set_title("Cross-Track Error Visualization")

    # Plot 2: XTE over simulation time/index (not distance)
    # Since we have different numbers of points, use simulation index
    simulation_indices = np.arange(len(xte_errors))
    ax2.plot(simulation_indices, xte_errors, "g-")
    ax2.set_xlabel("Simulation Point Index")
    ax2.set_ylabel("Cross-Track Error (m)")
    ax2.set_title("Cross-Track Error vs Simulation Time")
    ax2.grid(True)

    # Add horizontal lines for reference
    ax2.axhline(
        y=np.mean(xte_errors),
        color="r",
        linestyle="--",
        alpha=0.7,
        label=f"Mean: {np.mean(xte_errors):.1f}m",
    )
    ax2.axhline(
        y=np.percentile(xte_errors, 95),
        color="orange",
        linestyle="--",
        alpha=0.7,
        label=f"95%: {np.percentile(xte_errors, 95):.1f}m",
    )
    ax2.legend()

    plt.tight_layout()
    plt.show()


# Simple alternative if you still have issues
def quick_xte_analysis(hist_lats, hist_lons, sim_lats, sim_lons):
    """
    Simplified XTE analysis without complex plotting.
    """
    xte_errors, _ = calculate_cross_track_error_with_points(
        hist_lats, hist_lons, sim_lats, sim_lons
    )

    print("Quick XTE Analysis:")
    print(f"Mean XTE: {np.mean(xte_errors):.2f} m")
    print(f"Max XTE: {np.max(xte_errors):.2f} m")
    print(f"Std XTE: {np.std(xte_errors):.2f} m")
    print(f"95% XTE < {np.percentile(xte_errors, 95):.2f} m")

    # Simple histogram
    plt.figure(figsize=(10, 4))
    plt.hist(xte_errors, bins=50, alpha=0.7, edgecolor="black")
    plt.xlabel("Cross-Track Error (m)")
    plt.ylabel("Frequency")
    plt.title("Distribution of Cross-Track Errors")
    plt.grid(True, alpha=0.3)
    plt.show()

    return np.mean(xte_errors)


# Main execution
if __name__ == "__main__":
    # 1. Load your prepared historic tracks
    print("Loading prepared historic R tracks...")
    prepared_tracks_data = np.load("prepared_historic_tracksR.npz", allow_pickle=True)

    # Reconstruct the prepared_tracks dictionary properly
    prepared_tracks_dict = {}
    for key in prepared_tracks_data.files:
        # Each key corresponds to a track ID (H1, H2, H3)
        # The value is a dictionary stored as a numpy array
        track_dict = prepared_tracks_data[
            key
        ].item()  # Use .item() to get the dictionary
        prepared_tracks_dict[key] = track_dict

    print(f"Loaded historic tracks: {list(prepared_tracks_dict.keys())}")

    # Verify the structure
    for track_id, track_data in prepared_tracks_dict.items():
        print(
            f"{track_id}: {len(track_data.get('lats', []))} points, "
            f"Direction: {track_data.get('direction_group', 'Unknown')}"
        )

    # 2. Define your simulation JSON files
    simulation_files = {
        "sim_S1": "log_data S1 R Port.json",
        "sim_S2": "log_data -S2 R.json",
        "sim_S3": "log_data S3 R.json",
    }

    # 3. Compute RMSE
    rmse_results, loaded_simulations = compute_simulation_rmse(
        prepared_tracks_dict, simulation_files
    )

    # 4. Create summary DataFrame
    summary_data = []
    for hist_track_id, sim_results in rmse_results.items():
        for sim_id, metrics in sim_results.items():
            if metrics is not None:
                summary_data.append(
                    {
                        "Historic_Track": hist_track_id,
                        "Simulation_Run": sim_id,
                        "Direction": metrics["direction_match"],
                        "RMSE_m": metrics["rmse"],
                        "Max_Error_m": metrics["max_error"],
                        "Mean_Error_m": metrics["mean_error"],
                    }
                )

    rmse_summary_df = pd.DataFrame(summary_data)

    print("\n" + "=" * 60)
    print("SIMULATION RMSE SUMMARY")
    print("=" * 60)
    print(rmse_summary_df.to_string(index=False))

    # 5. Save results
    rmse_summary_df.to_csv("simulation_performance_resultsR.csv", index=False)
    print("\nResults saved to 'simulation_performance_resultsR.csv'")

    # 6. Compare with your CRLB benchmarks
    print("\n" + "=" * 60)
    print("COMPARISON WITH CRLB BENCHMARKS")
    print("=" * 60)
    print()

    for direction in ["Northbound", "Southbound"]:
        direction_mask = rmse_summary_df["Direction"] == direction
        if direction_mask.any():
            direction_rmse = rmse_summary_df[direction_mask]["RMSE_m"]
            avg_rmse = direction_rmse.mean()
            crlb = 3.062 if direction == "Northbound" else 2.236
            performance_ratio = avg_rmse / crlb

            print(f"{direction}:")
            print(f"  Average Simulation RMSE: {avg_rmse:.3f} m")
            print(f"  CRLB Benchmark:          {crlb:.3f} m")
            print(f"  Performance Ratio:       {performance_ratio:.2f}x")

            if performance_ratio < 1.2:
                print("  ✅ EXCELLENT: Near theoretical limit")
            elif performance_ratio < 1.5:
                print("  ✅ GOOD: Reasonable performance")
            elif performance_ratio < 2.0:
                print("  ⚠️  FAIR: Room for improvement")
            else:
                print("  ❌ POOR: Needs significant work")
            print()
# Simple test: distance between start points
hist_start_lat = prepared_tracks_dict["H3"]["lats"][0]
hist_start_lon = prepared_tracks_dict["H3"]["lons"][0]
sim_start_lat = loaded_simulations["sim_S3"]["lats"][0]
sim_start_lon = loaded_simulations["sim_S3"]["lons"][0]

simple_distance = haversine(
    hist_start_lat, hist_start_lon, sim_start_lat, sim_start_lon
)
print(f"Distance between start points: {simple_distance:.2f} m")

# Run the debugger
print("Debugging H1 track...")
hist_data = prepared_tracks_dict["H3"]
sim_data = loaded_simulations["sim_S3"]

debug_rmse_calculation_specific(
    hist_data["lats"], hist_data["lons"], sim_data["lats"], sim_data["lons"]
)
similarity = calculate_path_similarity(
    hist_data["lats"], hist_data["lons"], sim_data["lats"], sim_data["lons"]
)
print(f"Path Similarity Index: {similarity:.3f} (0-1 scale)")
performance_metrics = analyze_path_following_performance(
    hist_data["lats"], hist_data["lons"], sim_data["lats"], sim_data["lons"]
)

true_offset = calculate_true_lateral_offset(
    hist_data["lats"], hist_data["lons"], sim_data["lats"], sim_data["lons"]
)
print(f"True lateral offset: {true_offset:.2f} m")
print(f"Mean XTE from analysis: {performance_metrics['mean_xte']:.2f} m")
print(f"Max XTE from analysis: {performance_metrics['max_xte']:.2f} m")
print(f"95th percentile XTE from analysis: {performance_metrics['xte_95th']:.2f} m")
print(f"Path Similarity from analysis: {performance_metrics['similarity']:.3f}")
print(f"Number of XTE points analyzed: {performance_metrics['n_points']}")
