# Route Guidance and Trajectory Validation

## Line-of-Sight Route Guidance

The simulation connects mapped river geometry and port routes to vessel motion through region-specific reference paths:

- **Cuxhaven/Elbe:** The route builder joins the start and end positions to the selected river centerline and orders the centerline points for the travel direction.
- **Rheinhafen:** The port-aware route builder uses port polygons, port lines, and the river centerline to construct a route between the selected endpoints, including port-to-port and port-to-fairway transitions.
- **Reference path preparation:** The simulation can offset the route polyline in a metric coordinate system before passing the reference points to the motion controller.

Here, LOS means navigation guidance for following a reference route. It does not mean meteorological visibility or sensor-based obstacle detection.

## Route Following and Vessel Dynamics

At each simulation step, the controller compares the vessel's heading with the bearing to the current reference point and computes signed cross-track error relative to the reference segment. It uses those errors to set a bounded rudder angle and advances the reference point as the vessel approaches it. The propeller RPM ramps up at the start, and thrust is reduced during large rudder commands.

The motion update includes propeller thrust, hull drag, rudder forces, wind forces, and current forces. In the current implementation, wind can be fetched from the weather API and defaults to calm wind when no API key is configured. Current is a configured scenario input (currently 0.7 m/s from 200 degrees), rather than a live current feed. These force terms are model inputs and assumptions, not a claim that every environmental condition is dynamically sourced or calibrated.

## Vessel and Environmental Behaviour Analysis

The Cuxhaven and Rheinhaven analysis notebooks query AIS/environment tables and compare Speed Over Ground (SOG) across wind-hindrance conditions, vessel categories, and inbound/outbound directions. The Cuxhaven analysis also considers current hindrance. Visibility is used as a data-quality/operating-condition filter in the notebook queries rather than as a set of visibility-condition model outputs.

## Trajectory Preparation and Evaluation

The evaluation workflow prepares historical AIS tracks and compares them with simulated paths:

- **Common-distance interpolation:** Historical and simulated paths are resampled to a common normalized-distance grid before pointwise comparisons.
- **Position error:** RMSE is computed from Haversine distances between corresponding interpolated positions.
- **Path-shape similarity:** Pearson correlations are computed between successive latitude changes and successive longitude changes; their average is used as a shape-similarity score.
- **Cross-Track Error (XTE):** Each simulated point is compared with the closest segment of the historical path, with summary statistics reported in meters.
- **Visualization:** Folium maps display historical and simulated paths together. The Streamlit application provides interactive geographic views and Plotly charts.

## Implementation References

- [LOS route construction, guidance, and vessel-force simulation](../physics_basedv2.py)
- [Historical trajectory preparation](../Evaluation/CRLB_Data_prep.py)
- [Trajectory metrics and Folium comparison maps](../Evaluation/CRLB_Simulation.py)
- [Cuxhaven environmental and vessel analysis](../Analysis/Cuxhaven%20analysis.ipynb)
- [Rheinhaven environmental and vessel analysis](../Analysis/Rheinhaven%20analysis.ipynb)
- [Interactive Streamlit application](../streamlit_app.py)
