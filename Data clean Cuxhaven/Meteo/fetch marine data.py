import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry


class MarineWeatherFetcher:
    """
    Fetches marine weather data for specific dates (Mar 9-15 2025)
    """

    def __init__(self):
        # Setup cached session with retries
        cache_session = requests_cache.CachedSession(
            ".marine_cache", expire_after=3600, backend="sqlite"
        )
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.client = openmeteo_requests.Client(session=retry_session)
        self.base_url = "https://marine-api.open-meteo.com/v1/marine"

    def load_coordinates(self, filepath: str):
        """Load coordinates from CSV/text file"""
        try:
            if filepath.endswith(".csv"):
                df = pd.read_csv(filepath)
                # Auto-detect lat/lon columns (case insensitive)
                lat_col = [col for col in df.columns if "lat" in col.lower()][0]
                lon_col = [col for col in df.columns if "lon" in col.lower()][0]
                return list(zip(df[lat_col], df[lon_col]))
            else:  # Text file with lat,lon per line
                with open(filepath) as f:
                    return [
                        tuple(map(float, line.strip().split(",")))
                        for line in f
                        if line.strip()
                    ]
        except Exception as e:
            print(f"Error loading coordinates: {e}")
            return []

    def fetch_for_dates(self, coordinates: list):

        all_data = []

        params = {
            "hourly": [
                "wave_height",
                "wave_period",
                "wave_direction",
                "wind_wave_height",
                "wind_wave_direction",
                "ocean_current_velocity",
                "ocean_current_direction",
            ],
            "start_date": "2025-03-09",
            "end_date": "2025-03-15",
        }

        for lat, lon in coordinates:
            print(f"Fetching data for {lat}°N, {lon}°E...")
            try:
                # Update location-specific params
                location_params = params.copy()
                location_params.update({"latitude": lat, "longitude": lon})

                responses = self.client.weather_api(
                    self.base_url, params=location_params
                )
                response = responses[0]

                # Process hourly data
                hourly = response.Hourly()
                hourly_data = {
                    "date": pd.date_range(
                        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                        freq=pd.Timedelta(seconds=hourly.Interval()),
                        inclusive="left",
                    ),
                    "latitude": lat,
                    "longitude": lon,
                    "wave_height_m": hourly.Variables(0).ValuesAsNumpy(),
                    "wave_period_s": hourly.Variables(1).ValuesAsNumpy(),
                    "wave_direction_deg": hourly.Variables(2).ValuesAsNumpy(),
                    "wind_wave_height_m": hourly.Variables(3).ValuesAsNumpy(),
                    "wind_wave_direction_deg": hourly.Variables(4).ValuesAsNumpy(),
                    "current_velocity_mps": hourly.Variables(5).ValuesAsNumpy(),
                    "current_direction_deg": hourly.Variables(6).ValuesAsNumpy(),
                }

                df = pd.DataFrame(hourly_data)
                all_data.append(df)

            except Exception as e:
                print(f"Failed for {lat},{lon}: {str(e)}")
                continue

        return pd.concat(all_data) if all_data else pd.DataFrame()


# Example Usage
if __name__ == "__main__":
    fetcher = MarineWeatherFetcher()

    # Load coordinates (example: coords.csv with 'lat,lon' columns)
    coordinates = fetcher.load_coordinates("openmeteo_query_point_rhein.csv")

    if not coordinates:
        print("No valid coordinates found!")
    else:

        marine_data = fetcher.fetch_for_dates(coordinates)

        if not marine_data.empty:
            # Save to CSV
            output_file = "marine_weather_2025-03.csv"
            marine_data.to_csv(output_file, index=False)
            print(f"\n Saved data for {len(coordinates)} locations to {output_file}")

            # Print summary
            print("\nData Summary:")
            print(marine_data.groupby("latitude").size())

            # Sample data
            print("\nFirst 3 records:")
            print(marine_data.head(3))
        else:
            print("No data was fetched successfully")
