import json

# Load JSON
with open("log_data.json", "r", encoding="utf-8") as f:
    log_data = json.load(f)

# Define bounding box
min_lat, max_lat = 48.9664867153083, 48.966843207467015
min_lon, max_lon = 8.234228882101128, 8.235137640956296

# Filter
filtered_data = {
    step: entry
    for step, entry in log_data.items()
    if min_lat <= entry["latitude"] <= max_lat and
       min_lon <= entry["longitude"] <= max_lon
}

# Print
for step, entry in filtered_data.items():
    print(f"Step {step}: {entry}")
