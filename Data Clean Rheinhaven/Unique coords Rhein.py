import pandas as pd

# === CONFIGURATION ===
AIS_FILE = (
    "C:/Users/cvais/Documents/GitHub/AMS_ShipTraj/split_output/position_reports.csv"
)
OUTPUT_POINTS_FILE = "openmeteo_query_point_rhein.csv"
ROUND_DECIMALS = 2  # 0.01° resolution for Open-Meteo

# === Load AIS Data ===
df = pd.read_csv(AIS_FILE)

# === Round Latitude and Longitude to Open-Meteo resolution ===
df["lat_openmeteo"] = df["lat"].round(ROUND_DECIMALS)
df["lon_openmeteo"] = df["lon"].round(ROUND_DECIMALS)

# === Extract unique Open-Meteo-compatible coordinates ===
query_points = (
    df[["lat_openmeteo", "lon_openmeteo"]].drop_duplicates().reset_index(drop=True)
)
query_points.columns = ["latitude", "longitude"]  # for API compatibility

# === Save to CSV ===
query_points.to_csv(OUTPUT_POINTS_FILE, index=False)

print(f" Open-Meteo query points saved to: {OUTPUT_POINTS_FILE}")
print(f"Total unique query points (0.1° grid): {len(query_points)}")
