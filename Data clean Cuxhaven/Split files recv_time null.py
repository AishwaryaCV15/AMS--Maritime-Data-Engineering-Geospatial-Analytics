import csv


def filter_ais_data(input_file, valid_output_file, invalid_output_file):
    # Define headers based on your input file
    headers = [
        "UserID",
        "RAIM-flag",
        "Latitude",
        "SOG",
        "Navigationalstatus",
        "Longitude",
        "Specialmanoeuvreindicator",
        "Trueheading",
        "RateofturnROTAIS",
        "Timestamp",
        "Repeatindicator",
        "COG",
        "MessageID",
        "Positionaccuracy",
        "recv_time",
        "ClassBdisplayflag",
        "ClassBbandflag",
        "ClassBunitflag",
        "Communicationstateselectorflag",
        "ClassBMessage22flag",
        "Modeflag",
        "ClassBDSCflag",
    ]

    with open(input_file, "r") as infile, open(
        valid_output_file, "w", newline=""
    ) as valid_out, open(invalid_output_file, "w", newline="") as invalid_out:

        reader = csv.reader(infile)
        valid_writer = csv.writer(valid_out)
        invalid_writer = csv.writer(invalid_out)

        # Write headers to both files
        valid_writer.writerow(headers)
        invalid_writer.writerow(headers)

        for row in reader:
            if len(row) != len(headers):
                continue  # Skip malformed rows

            latitude = row[2]
            longitude = row[5]
            recv_time = row[14]

            # Check if line meets criteria for valid file
            if latitude != "ERROR" and longitude != "ERROR" and recv_time != "0":
                valid_writer.writerow(row)
            else:
                invalid_writer.writerow(row)

    print("Successfully filtered data:")
    print(f"- Valid data written to: {valid_output_file}")
    print(f"- Invalid data written to: {invalid_output_file}")


# Example usage
if __name__ == "__main__":
    input_file = "D:/ovgu/sem3/AMS/DataCleaner/message_main.csv"
    valid_output_file = "valid_ais_data.csv"
    invalid_output_file = "invalid_ais_data.csv"

    filter_ais_data(input_file, valid_output_file, invalid_output_file)
