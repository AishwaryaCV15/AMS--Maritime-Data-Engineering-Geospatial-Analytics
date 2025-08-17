import pandas as pd


def process_ais_data(input_file, output_file):
    # Load the data
    df = pd.read_csv(input_file)

    print("Original columns:", df.columns.tolist())
    print("Initial shape:", df.shape)

    # Convert recv_time to numeric (handling errors and zeros)
    df["recv_time"] = pd.to_numeric(df["recv_time"], errors="coerce")
    df = df[df["recv_time"] > 0].copy()  # Remove invalid/zero timestamps

    # Convert recv_time from milliseconds to datetime objects (UTC)
    df["datetime_utc"] = pd.to_datetime(df["recv_time"], unit="ms", errors="coerce")

    # Remove any rows where datetime conversion failed
    df = df[df["datetime_utc"].notna()].copy()

    # Sort by UserID and recv_time
    df = df.sort_values(by=["UserID", "recv_time"])

    # Interpolate missing timestamps per user (using your robust method)
    def interpolate_user_times(group):
        result = group.copy()
        result["unix_time"] = result["datetime_utc"].astype(int) // 10**9
        result["unix_interpolated"] = result["unix_time"].interpolate(method="linear")
        result["datetime_interpolated"] = (
            pd.to_datetime(result["unix_interpolated"], unit="s", errors="coerce")
            .ffill()
            .bfill()
        )
        return result.drop(columns=["unix_time", "unix_interpolated"])

    # Apply interpolation per user
    processed_groups = []
    for user_id, group in df.groupby("UserID"):
        processed_groups.append(interpolate_user_times(group))
    df = pd.concat(processed_groups, ignore_index=True)

    # Select and order output columns
    output_columns = [
        "UserID",
        "datetime_utc",
        "datetime_interpolated",
        "recv_time",
        "Latitude",
        "Longitude",
        "SOG",
        "COG",
        "Trueheading",
        "Navigationalstatus",
        "MessageID",
        "RAIM-flag",
        "Name",
        "Call sign",
        "Specialmanoeuvreindicator",
        "RateofturnROTAIS",
        "Timestamp",
        "Positionaccuracy",
    ]
    # Only include columns that exist in the dataframe
    output_columns = [col for col in output_columns if col in df.columns]

    # Save to CSV
    df[output_columns].to_csv(output_file, index=False)

    print(f"\nProcessing complete. Results saved to {output_file}")
    print(f"Final shape: {df.shape}")
    print(f"Number of unique vessels: {df['UserID'].nunique()}")


if __name__ == "__main__":
    process_ais_data(
        input_file="valid_ais_data.csv",  # Replace with your input file
        output_file="utc_ais_data_1.csv",
    )
