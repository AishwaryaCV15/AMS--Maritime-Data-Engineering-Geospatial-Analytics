# Geospatial Data Preparation and Boundary Creation

## Purpose

Geospatial preparation defined the Cuxhaven/Elbe and Rhein Haven study areas and provided geographic context for filtering AIS observations. The project keeps both OpenStreetMap (OSM) reference layers exported from Overpass Turbo and the operational polygons used by the AIS preprocessing scripts.

These are related, but not identical, assets: the GeoJSON files describe mapped rivers, navigation marks, ports, anchorages, and other features; the filtering scripts also contain explicit study-area polygon coordinates used to select AIS points.

## Boundary Workflow

1. **Explore the study regions.** Overpass Turbo queries define a geographic bounding box or polygon and request relevant OSM features, including waterways/fairways, buoys and beacons, ports, marinas, anchorages, bridges, and ferry infrastructure. The query files are kept beside the exported layers so the source selection can be reviewed.
2. **Export and inspect GeoJSON.** Export the Overpass results as GeoJSON and inspect the waterway geometry and surrounding navigation features. The exports are reference layers for understanding the study area and making boundary decisions; they are not all AIS-filter polygons.
3. **Define the AIS study polygon.** Select an ordered set of longitude/latitude vertices for each study region. The Cuxhaven and Rhein preprocessing scripts build Shapely `Polygon` objects from these coordinates. Where the analysis excludes selected areas such as anchorages, the Cuxhaven script combines exclusion polygons and filters out points inside them.
4. **Filter AIS positions spatially.** Convert the polygon to WKT and query MySQL with `ST_Within(POINT(longitude, latitude), polygon)`. This produces region-specific AIS records for downstream encounter, environmental, and trajectory analysis. The Rhein script uses the corresponding `lon` and `lat` columns.
5. **Visualize working boundaries.** The Streamlit app loads display polygons from `Data/boundary.json` and `Data/Cuxhaven_bounding_box.json` and draws them on its map. Keep these display boundaries consistent with the areas used in preprocessing when updating the study regions.

## Repository Artifacts

### Cuxhaven / Elbe

- [Overpass query for Cuxhaven maritime features](../Boundary%20Files/cuxhaven%20all%20query.overpassql)
- [Cuxhaven river line GeoJSON](../Boundary%20Files/Cuxhaven%20Main%20River%20line.geojson)
- [Cuxhaven mapped features GeoJSON](../Boundary%20Files/Cuxhaven%20Map%20all.geojson)
- [Cuxhaven markings GeoJSON](../Boundary%20Files/cuxhaven%20all%20markings.geojson)
- [Cuxhaven environmental study polygon GeoJSON](../Boundary%20Files/cuxhaven_Boundary_evn_polygon.geojson)
- [Cuxhaven AIS polygon filtering](../Data%20clean%20Cuxhaven/ais%20in%20polygon.py)
- [Cuxhaven anchorage exclusion](../Data%20clean%20Cuxhaven/Ais%20outside%20Anchorage.py)

### Rhein Haven

- [Overpass query for Rhein study region](../Boundary%20Files/Rheinhaven%20Polygon%20query%20all.overpassql)
- [Rheinhaven polygon/features GeoJSON](../Boundary%20Files/Rheinhaven%20Polygon%20all.geojson)
- [Lower Rhein area GeoJSON](../Boundary%20Files/rhein%20lower%20area.geojson)
- [Rheinhaven port markings GeoJSON](../Boundary%20Files/Rheinhaven%20Karlsruhe%20Port%20marking.geojson)
- [Rhein AIS polygon filtering](../Data%20Clean%20Rheinhaven/Rhein%20ais%20in%20polygon.py)

### Map Display

- [Rhein display boundaries](../Data/boundary.json)
- [Cuxhaven display boundary](../Data/Cuxhaven_bounding_box.json)
- [Interactive map application](../streamlit_app.py)

## Reproducibility Notes

GeoJSON coordinates use longitude/latitude order, matching the `[longitude, latitude]` tuples in the filtering scripts. The Overpass query files and exported GeoJSON layers preserve the geographic context used during boundary selection. When revising a study region, update and review the Overpass query/export, operational preprocessing polygon, and app display boundary together; otherwise the displayed and filtered regions can diverge.
