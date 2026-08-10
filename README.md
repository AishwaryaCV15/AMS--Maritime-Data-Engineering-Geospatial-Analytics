# Simulation and Analysis of Ship Trajectories

## Project Team

- Aishwarya Chincholi Vasant Madhav
- Nishanth Battu
- Vineet Agarwal

## Mentor

- Taruna Tiwari

## Project Milestones Summary

- **M1: Planning and Literature Review (Early May 2025, 2 weeks)**: All three team members reviewed literature on ship trajectory prediction, physics-based maneuvering models, AIS-based environmental analysis, and data-driven approaches.
- **M2: AIS Data EDA and Git Setup (Mid-May to Late May 2025, 3 weeks)**: All three members contributed to initial EDA. Aishwarya set up the GitHub repository, supported data cleaning, and analyzed environmental factors.
- **M3: Model Creation and Simulation (Early June to Early July 2025, 5 weeks)**: Nishanth developed the physics-based ship motion model. Aishwarya developed the line-of-sight planning logic used by the model.
- **M4: Model Validation (Early July to Mid-July 2025, 2 weeks)**: Nishanth led model validation, while Vineet validated edge cases across different start and end point scenarios.
- **M5: UI Refinement and Interactive Map (Mid-July to Mid-August 2025, 4 weeks)**: Vineet developed the interactive UI and map-based simulation workflow.
- **M6: Evaluation and Refinement (Mid-August to Late August 2025, 2 weeks)**: Aishwarya and Nishanth evaluated and refined the physics-based model against ground-truth AIS trajectories, while Vineet refined the UI based on model updates.
- **M7: Scientific Writing, Reporting, and Presentation (June to September 2025, parallel)**: All three members documented their respective work. Vineet proofread and maintained the overall report structure and tone.

## Description
A sophisticated simulation framework for ship trajectory modeling that combines physics-based dynamics with historical Automatic Identification System (AIS) data to replicate realistic vessel behavior under varying environmental conditions. This hybrid approach bridges theoretical modeling with practical data-driven insights to advance maritime intelligence and safety.

Core Purpose: Understanding and predicting maritime vessel movement is critical for ensuring navigational safety, efficient port operations, and effective environmental oversight. Our framework addresses this need by integrating real-world navigation patterns with environmental variables to create highly realistic ship behavior simulations.

Key Innovation: Unlike traditional approaches that rely solely on either physics models or statistical methods, our hybrid methodology leverages both:

Physics-based dynamics for fundamental vessel behavior

Historical AIS data analysis for weather impact

Environmental variable integration for condition-specific performance. 

## Streamlit App Deployment

The Streamlit app entrypoint for deployment is:

```text
streamlit_app.py
```

You can deploy this repository directly from GitHub on Streamlit Community Cloud. A dev container is not required for hosting.

### Optional: Enable live wind data

The app can use OpenWeather live wind data when an API key is available. If no key is configured, the simulation falls back to calm wind.

For Streamlit Community Cloud, add this secret in your app settings:

```toml
OPENWEATHER_API_KEY = "your_openweather_api_key"
```

For local development, create:

```text
.streamlit/secrets.toml
```

You can copy the format from:

```text
.streamlit/secrets.toml.example
```

### Visible authorship in the deployed app

The deployed Streamlit UI explicitly shows the project team so all contributors are credited in the app itself, independent of GitHub contributor graph behavior.

## Weather Data analysis

The `Analysis/` folder contains:

- `Analysis/Cuxhaven analysis.ipynb`
- `Analysis/Rheinhaven analysis.ipynb`

The Jupyter Notebook analyzes ship Speed Over Ground (SOG) performance and ship size pattern under various environmental hindrance conditions (wind and current) for different navigation directions.

## Features

- **Database Integration**: Connects to MySQL AIS database
    
- **Environmental Analysis**: Examines wind and current hindrance effects
    
- **Directional Analysis**: Compares inbound vs outbound ship performance
    
- **Visualization**: Box plots and bar charts for performance comparison
    
- **Statistical Aggregation**: Mean SOG calculations and delta comparisons

## Requirements

```bash
pip install mysql-connector-python pandas numpy seaborn matplotlib
```

## Database Configuration

```python
db_config = {
    "host": "localhost",
    "user": "root", 
    "password": "your_password_here",
    "database": "ship_data",
}
```

## Evaluation of physics based ship trajectory model
A complete pipeline for analyzing ship path following performance, from data preparation to simulation comparison.

Note: The evaluation scripts depend on a local MySQL/database setup and the required input data files. The documentation in this README is aligned with the current repository structure, but those scripts will only run when the local database configuration and source data are available.

## System Overview

This system consists of two main components:

1. **File 1: Data Preparation Script** (`Evaluation/CRLB_Data_prep.py`) - Loads and processes historic ship tracks from database
2. **File 2: Analysis Tool** (`Evaluation/CRLB_Simulation.py`) - Compares simulated paths against historic references

## Quick Start

### 1. Install Dependencies
```bash
pip install numpy pandas scipy matplotlib folium shapely mysql-connector-python
```

### 2. Run Data Preparation (File 1)
```bash
# Run from the repository root
# Modify database credentials in Evaluation/CRLB_Data_prep.py
python Evaluation/CRLB_Data_prep.py
```
**Output**: `prepared_historic_tracks.npz`, `track_summary.csv`

### 3. Run Path Analysis (File 2)
```bash
# Run from the repository root
# Modify simulation file paths in Evaluation/CRLB_Simulation.py
python Evaluation/CRLB_Simulation.py
```
**Output**: Performance metrics, visualizations, and comparison reports

## File 1: Data Preparation Script (`Evaluation/CRLB_Data_prep.py`)

### Purpose
Loads historic ship tracks from MySQL database and prepares them for analysis.

### Key Features
- **Database Connection**: Fetches AIS data for specific ships and time windows
- **Coordinate Conversion**: Transforms lat/lon to local Cartesian coordinates (meters)
- **Direction Classification**: Labels tracks as Northbound/Southbound based on bearing
- **Noise Estimation**: Calculates empirical GPS noise (CRLB) for performance benchmarking

### Input Requirements
- MySQL database with AIS data table named `ais_open_water_polygon_env`
- Database credentials (host, user, password, database)
- Ship MMSI numbers and time windows defined in `tracks_to_load`

### Configuration
```python
db_config = {
    "host": "localhost",
    "user": "root", 
    "password": "your_password_here",
    "database": "ship_data",
}

tracks_to_load = [
    {
        "mmsi": 304814000,
        "start_time": "2025-04-27 06:59:17",
        "end_time": "2025-04-27 07:32:19", 
        "id": "H1",
    },
    # ... more tracks
]
```

### Output Files
- `prepared_historic_tracks.npz` - Processed tracks with coordinates, distances, directions
- `track_summary.csv` - Statistics for each track (duration, distance, speed, etc.)

### Data Structure
Each track contains:
```python
{
    'mmsi': ship_identifier,
    'times': timestamps, 
    'lats': latitudes,
    'lons': longitudes,
    'sogs': speeds_over_ground,
    'headings': true_headings,
    'x': local_x_coordinates_meters,
    'y': local_y_coordinates_meters,
    'distances': cumulative_distances_meters,
    'ref_point': reference_coordinates,
    'direction_group': "Northbound"/"Southbound",
    'bearing': compass_bearing_degrees
}
```

---

## File 2: Path Evaluation (`Evaluation/CRLB_Simulation.py`)

### Purpose
Compares simulated ship paths against prepared historic tracks and evaluates performance.

### Key Features
- **Multi-track Analysis**: Compare multiple simulations against multiple historic tracks
- **Comprehensive Metrics**: RMSE, Cross-Track Error (XTE), path similarity index
- **Visualization**: Interactive Folium maps, error plots, path comparisons
- **Performance Benchmarking**: Compare against CRLB theoretical limits
- **Debugging Tools**: Detailed analysis of path discrepancies

### Input Requirements
- `prepared_historic_tracks.npz` from File 1 data preparation
- Simulation JSON files with timestamped position data

### Configuration
```python
# For standard analysis
simulation_files = {
    "sim_S1": "log_data-S1 down.json",
    "sim_S2": "log_data-S2 up.json", 
    "sim_S3": "log_data-S3 up.json",
}

# For R tracks analysis  
simulation_files = {
    "sim_S1": "log_data S1 R Port.json",
    "sim_S2": "log_data -S2 R.json",
    "sim_S3": "log_data S3 R.json",
}
```

### Supported Simulation Format
```json
{
    "point_1": {
        "timestamp": 1234567890.0,
        "latitude": 40.123456,
        "longitude": -74.123456,
        "x_velocity": 0.0,
        "y_velocity": 0.0,
        "heading": 45.0
    }
}
```

### Output Files
- `simulation_performance_results.csv` - All performance metrics in table format
- `true_scale_comparison.html` - Interactive Folium map for path visualization
- Console output with color-coded performance assessment
- Matplotlib plots of cross-track errors and distributions

### Key Analysis Functions
- `compute_simulation_rmse()` - Main RMSE calculation
- `analyze_path_following_performance()` - Comprehensive XTE analysis  
- `calculate_path_similarity()` - Shape correlation (0-1 scale)
- `debug_rmse_calculation_specific()` - Problem diagnosis tool

## Complete Workflow

1. **Prepare Historic Data**: Run `Evaluation/CRLB_Data_prep.py` to load and process database tracks
2. **Generate Simulations**: Run your controller to produce simulation JSON files
3. **Analyze Performance**: Run `Evaluation/CRLB_Simulation.py` to compare simulations against historic data
4. **Review Results**: Check CSV reports, interactive maps, and console assessments
5. **Debug Issues**: Use built-in debugging tools for problematic comparisons
