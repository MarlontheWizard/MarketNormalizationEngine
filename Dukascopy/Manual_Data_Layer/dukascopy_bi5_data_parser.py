import os
import lzma
import struct
import pandas as pd
from datetime import datetime, timedelta


TICK_STRUCT = ">3I2f"
TICK_SIZE = struct.calcsize(TICK_STRUCT)


def decompress_bi5(file_path: str) -> bytes:
    
    #Unzip .bi5 file

    with lzma.open(file_path, "rb") as f:
        return f.read()


def parse_tick_data(binary_data: bytes, hour_start: datetime) -> list:

    #Data is now unzipped - Proceed to parse tick binary data

    ticks = []

    for offset in range(0, len(binary_data), TICK_SIZE):

        chunk = binary_data[offset:offset + TICK_SIZE]

        if len(chunk) != TICK_SIZE:
            
            continue

        ms_offset, ask, bid, ask_volume, bid_volume = struct.unpack(TICK_STRUCT, chunk)

        timestamp = hour_start + timedelta(milliseconds=ms_offset)

        ticks.append({
            "timestamp": timestamp,
            "bid": bid / 100000,
            "ask": ask / 100000,
            "bid_volume": bid_volume,
            "ask_volume": ask_volume
        })

    return ticks


def build_dataframe(ticks: list) -> pd.DataFrame:
    
    #Convert tick list into a dataframe

    return pd.DataFrame(ticks)


def extract_datetime_from_filename(file_name: str) -> datetime:
    
    #Example filename: EURUSD_20240102_03h.bi5

    parts = file_name.replace(".bi5", "").split("_")

    date_part = parts[1]
    hour_part = parts[2].replace("h", "")

    return datetime.strptime( f"{date_part}{hour_part}", "%Y%m%d%H" )


def process_file(file_path: str):

    file_name = os.path.basename(file_path)

    print(f"[BEGIN] Processing {file_name}")

    hour_start = extract_datetime_from_filename(file_name)

    binary_data = decompress_bi5(file_path)

    ticks = parse_tick_data(binary_data, hour_start)

    df = build_dataframe(ticks)

    print(df.head())

    return df


def main():

    file_path = (
        "bi5_data/"
        "EURUSD/"
        "2024-01-02/"
        "EURUSD_20240102_03h.bi5"
    )

    process_file(file_path)


if __name__ == "__main__":

    main()