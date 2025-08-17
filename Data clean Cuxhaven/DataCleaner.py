import csv
import glob
import re

main_headers = [
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

message5_headers = [
    "Destination",
    "UserID",
    "Maximumpresentstaticdraught",
    "Typeofelectronicpositionfixingdevice",
    "Name",
    "ETA",
    "DTE",
    "DimensionD",
    "DimensionC",
    "DimensionB",
    "DimensionA",
    "Repeatindicator",
    "Typeofshipandcargotype",
    "IMOnumber",
    "MessageID",
    "AISversionindicator",
    "Callsign",
    "recv_time",
]

message24_headers = [
    "UserID",
    "VendorID",
    "Typeofelectronicpositionfixingdevice",
    "DimensionD",
    "DimensionC",
    "DimensionB",
    "DimensionA",
    "Repeatindicator",
    "Typeofshipandcargotype",
    "MessageID",
    "Callsign",
    "Name",
    "recv_time",
]

output_main = "message_main.csv"
output_5 = "message_5.csv"
output_24 = "message_24.csv"

space_regex = re.compile(" ")
cleaner_regex = re.compile(r"\\n|\"\{|\}|\\")


def clean_line(line):
    line = cleaner_regex.sub("", line)
    line = space_regex.sub("", line)
    line = line.replace('"', "")
    return line


def write_headers(writer, headers):
    writer.writerow(headers)


def process_message(line, headers, writer):
    key_index = {key: i for i, key in enumerate(headers)}
    fields = line.split(",")
    row = [0] * len(key_index)

    for field in fields:
        if ":" not in field:
            continue
        key, val = field.split(":", 1)

        if key == "Latitude":
            try:
                v = float(val)
                if not -90 <= v <= 90:
                    val = "ERROR"
            except ValueError:
                val = "ERROR"

        elif key == "Longitude":
            try:
                v = float(val)
                if not -180 <= v <= 180:
                    val = "ERROR"
            except ValueError:
                val = "ERROR"

        if key in key_index:
            row[key_index[key]] = val

    writer.writerow(row)


def process_line(line, writers):
    line = clean_line(line)

    if "MessageID:5" in line:
        process_message(line, message5_headers, writers["5"])
    elif "MessageID:24" in line:
        process_message(line, message24_headers, writers["24"])
    else:
        process_message(line, main_headers, writers["main"])


def process_file(path, writers):
    with open(path, "r") as f:
        for line in f:
            process_line(line.strip(), writers)


def main():
    with open(output_main, "w", encoding="utf-8", newline="") as f_main, open(
        output_5, "w", encoding="utf-8", newline=""
    ) as f_5, open(output_24, "w", encoding="utf-8", newline="") as f_24:

        writer_main = csv.writer(f_main)
        writer_5 = csv.writer(f_5)
        writer_24 = csv.writer(f_24)

        # Write headers
        write_headers(writer_main, main_headers)
        write_headers(writer_5, message5_headers)
        write_headers(writer_24, message24_headers)

        writers = {"main": writer_main, "5": writer_5, "24": writer_24}

        # TODO CHANGE THE DIRECTORY TO SPLIT FILES DIRECTORY
        # USE `split -n 893 dlr_ais_messages.txt` on Linux/WSL
        files = glob.glob(
            "D:/ovgu/sem3/AMS/Data/Cuxhafen AIS data/Cuxhafen AIS data/dlr_ais_messages/test_split/*.txt"
        )

        for path in files:
            process_file(path, writers)

    print("Processing complete.")


if __name__ == "__main__":
    main()
