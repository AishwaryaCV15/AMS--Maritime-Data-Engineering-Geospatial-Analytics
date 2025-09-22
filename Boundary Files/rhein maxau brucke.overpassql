// Straight Rhine section (Karlsruhe–Maxau), include aids + obstructions + ferries
[out:json][timeout:60];

(
  // Core fairway and river line
  way["waterway"="fairway"](49.05, 8.30, 49.12, 8.40);
  way["waterway"="river"](49.05, 8.30, 49.12, 8.40);

  // Navigational aids
  nwr["seamark:type"~"buoy_lateral|buoy_cardinal|buoy_isolated_danger|buoy_safe_water"](49.05, 8.30, 49.12, 8.40);
  nwr["seamark:type"~"beacon_lateral|beacon_cardinal|light|light_vessel|special_purpose"](49.05, 8.30, 49.12, 8.40);

  // Lateral marks (port/starboard)
  nwr["seamark:buoy_lateral:category"](49.05, 8.30, 49.12, 8.40);
  nwr["seamark:beacon_lateral:category"](49.05, 8.30, 49.12, 8.40);

  // Maritime/river infra
  nwr["man_made"~"pier|jetty|dock"](49.05, 8.30, 49.12, 8.40);
  nwr["harbour"="yes"](49.05, 8.30, 49.12, 8.40);
  nwr["leisure"="marina"](49.05, 8.30, 49.12, 8.40);
  nwr["seamark:type"~"anchorage|mooring"](49.05, 8.30, 49.12, 8.40);
  way["waterway"="dock"](49.05, 8.30, 49.12, 8.40);
  relation["landuse"="harbour"](49.05, 8.30, 49.12, 8.40);

  // Bridges (possible choke points)
  nwr["bridge"](49.05, 8.30, 49.12, 8.40);

  // 🚫 Ferries (detect to avoid area)
  way["route"="ferry"](49.05, 8.30, 49.12, 8.40);
  node["amenity"="ferry_terminal"](49.05, 8.30, 49.12, 8.40);
);

out geom;
