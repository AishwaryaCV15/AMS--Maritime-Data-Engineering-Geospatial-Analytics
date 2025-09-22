[out:json][timeout:60];

// Define the bounding box for Cuxhaven to Brunsbüttel
(
  // Navigational aids, including beacons and buoys
  nwr["seamark:type"="buoy_lateral"](53.8, 8.6, 54.1, 9.2);      // Lateral buoys (port/starboard)
  nwr["seamark:type"="buoy_cardinal"](53.8, 8.6, 54.1, 9.2);     // Cardinal buoys
  nwr["seamark:type"="buoy_isolated_danger"](53.8, 8.6, 54.1, 9.2); // Isolated danger buoys
  nwr["seamark:type"="buoy_safe_water"](53.8, 8.6, 54.1, 9.2);    // Safe water buoys
  nwr["seamark:type"="beacon_lateral"](53.8, 8.6, 54.1, 9.2);    // Lateral beacons
  nwr["seamark:type"="beacon_cardinal"](53.8, 8.6, 54.1, 9.2);   // Cardinal beacons
  nwr["seamark:type"="light"](53.8, 8.6, 54.1, 9.2);              // Navigational lights (as standalone objects)
  nwr["seamark:type"="light_vessel"](53.8, 8.6, 54.1, 9.2);      // Light vessels (lightships)
  nwr["seamark:type"="special_purpose"](53.8, 8.6, 54.1, 9.2);   // Special purpose buoys/beacons

  // Fairways and channels
  way["waterway"="fairway"](53.8, 8.6, 54.1, 9.2);

  // Other maritime infrastructure
  nwr["harbour"="yes"](53.8, 8.6, 54.1, 9.2);
  nwr["leisure"="marina"](53.8, 8.6, 54.1, 9.2);
  nwr["seamark:type"="anchorage"](53.8, 8.6, 54.1, 9.2);
  nwr["man_made"="pier"](53.8, 8.6, 54.1, 9.2);
  nwr["man_made"="jetty"](53.8, 8.6, 54.1, 9.2);
  nwr["man_made"="dock"](53.8, 8.6, 54.1, 9.2);
  nwr["waterway"="dock"](53.8, 8.6, 54.1, 9.2);

  // Markings for port and starboard sides (lateral marks)
  // These are often secondary tags on the buoy/beacon itself,
  // but we can query them directly as a broader catch.
  nwr["seamark:buoy_lateral:category"="port"](53.8, 8.6, 54.1, 9.2);
  nwr["seamark:buoy_lateral:category"="starboard"](53.8, 8.6, 54.1, 9.2);
  nwr["seamark:beacon_lateral:category"="port"](53.8, 8.6, 54.1, 9.2);
  nwr["seamark:beacon_lateral:category"="starboard"](53.8, 8.6, 54.1, 9.2);

);
out geom;