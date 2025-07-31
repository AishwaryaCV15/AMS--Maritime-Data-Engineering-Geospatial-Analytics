import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry


class MarineWeatherFetcher:
    """
    Fetches marine weather data for specific dates (Feb 6-7, 2025)
    """

    def __init__(self):
        # Setup cached session with retries
        cache_session = requests_cache.CachedSession(
            ".cache", expire_after=3600, backend="sqlite"
        )
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.client = openmeteo_requests.Client(session=retry_session)
        self.base_url = "https://historical-forecast-api.open-meteo.com/v1/forecast"

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
        """Fetch data for Feb 6-7, 2025 specifically"""
        all_data = []

        # Define hourly parameters in specific order
        hourly_params = [
            "temperature_2m",
            "wind_speed_10m",
            "visibility",
            "wind_speed_80m",
            "wind_speed_120m",
            "wind_speed_180m",
            "wind_direction_10m",
            "wind_direction_80m",
            "wind_direction_120m",
            "wind_direction_180m",
            "wind_gusts_10m",
            "temperature_80m",
        ]

        params = {
            "hourly": hourly_params,
            "start_date": "2025-04-15",
            "end_date": "2025-04-29",
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

                # Create base data structure
                hourly_data = {
                    "date": pd.date_range(
                        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                        freq=pd.Timedelta(seconds=hourly.Interval()),
                        inclusive="left",
                    ),
                    "latitude": lat,
                    "longitude": lon,
                }

                # Map each parameter to its correct index
                for i, param in enumerate(hourly_params):
                    column_name = f"hourly_{param}"
                    # Fix the visibility column name (remove extra space)
                    if param == "visibility":
                        column_name = "hourly_visibility"
                    hourly_data[column_name] = hourly.Variables(i).ValuesAsNumpy()

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
    coordinates = fetcher.load_coordinates("openmeteo_query_points.csv")

    if not coordinates:
        print("No valid coordinates found!")
    else:
        # Fetch data for Feb 6-7, 2025
        weather_data = fetcher.fetch_for_dates(coordinates)

        if not weather_data.empty:
            # Save to CSV
            output_file = "weather_2025-04.csv"
            weather_data.to_csv(output_file, index=False)
            print(f"\n Saved data for {len(coordinates)} locations to {output_file}")

            # Print summary
            print("\nData Summary:")
            print(weather_data.groupby("latitude").size())

            # Sample data
            print("\nFirst 3 records:")
            print(weather_data.head(3))
        else:
            print("No data was fetched successfully")
