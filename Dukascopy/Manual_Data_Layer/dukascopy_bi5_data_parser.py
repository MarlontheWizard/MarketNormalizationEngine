import os
import lzma
import struct
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


TICK_STRUCT = ">3I2f"
TICK_SIZE = struct.calcsize(TICK_STRUCT)

    
def decompress_bi5(file) -> bytes:
    
    #Unzip .bi5 file

    with lzma.open(file, "rb") as f:
        return f.read()
      

def parse_tick_data(binary_data: bytes, hour_start: datetime) -> list:

    #we have the file bytes in a dataframe - proceed to parse tick binary data

    ticks = []

    for offset in range(0, len(binary_data), TICK_SIZE):

        chunk = binary_data[offset:offset + TICK_SIZE]

        if len(chunk) != TICK_SIZE:
            
            continue

        millisec_offset, ask, bid, ask_volume, bid_volume = struct.unpack(TICK_STRUCT, chunk)

        timestamp = hour_start + timedelta(milliseconds=millisec_offset)

        ticks.append({
            "timestamp": timestamp,
            "bid": bid / 100000,
            "ask": ask / 100000,
            "bid_volume": bid_volume,
            "ask_volume": ask_volume
        })

    return ticks


def build_dataframe(ticks: list) -> pd.DataFrame:
    
    #convert tick list into a dataframe

    return pd.DataFrame(ticks)
    

def extract_datetime_from_filename(file_name: str) -> datetime:
    
    #Example filename: EURUSD_20240102_03h.bi5

    parts = file_name.replace(".bi5", "").split("_")

    date_part = parts[1]
    hour_part = parts[2].replace("h", "")

    return datetime.strptime( f"{date_part}{hour_part}", "%Y%m%d%H" )

    
def create_dataframe(file_path: str):

    file_name = os.path.basename(file_path)

    #dukascopy stores timestamps as milliseconds offset from the beginning of the hour
    hour_start = extract_datetime_from_filename(file_name)

    #returns binary bytes
    binary_data = decompress_bi5(file_path)

    #parse binary tick records
    ticks = parse_tick_data(binary_data, hour_start)

    df = build_dataframe(ticks)

    return df
    

def find_bi5_files(root_dir: str) -> list:

    #recursively find all files
    
    bi5_files = []

    for root, _, files in os.walk(root_dir):

        for file in files:

            if file.endswith(".bi5"):

                bi5_files.append(
                    os.path.join(root, file)
                )

    return sorted(bi5_files)


def save_dataframe(df, file_path, data_root_path, output_path):

    #keep relative structure after bi5_data
    relative_path = os.path.relpath(file_path, data_root_path)

    #keeps original filename
    output_file = os.path.join(output_path, relative_path).replace(".bi5", ".parquet")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    df.to_parquet(output_file, index=False)

    #print(f"[SAVED] {output_path}")
    

def process_file(files, data_root_path, output_path):    

    try:
        
        df = create_dataframe(file)

        save_dataframe(df, file, data_root_path, output_path)

        return None

    except Exception as e:

        return (file, str(e))


def process_files(files, data_root_path, output_path, threads):

    with ThreadPoolExecutor(max_workers=threads) as executor:

        future_results = [executor.submit(process_single_file, file, data_root_path, output_path) for file in files]

        with tqdm(total=len(files), desc="Parsing BI5 → Parquet") as pbar:

            for f in as_completed(future_results):

                result = f.result()

                if result is not None:
                    
                    file, error = result
                    print(f"[PARSER FAILED] {file}")
                    print(error)

                pbar.update(1)


def begin_parser_process(args):

   print(f"[PARSER START] Beginning parsing process for stored raw data in {args.raw_data_dir}...")

   zipped_files = find_bi5_files(args.raw_data_dir)

   process_files(zipped_files, args.raw_data_dir, args.parsed_data_dir, args.threads)

   print(f"[PARSER END] Raw data parsed successfully to {args.parsed_data_dir}.")



''' Uncomment to facilitate direct isolated testing  
def main():

    begin_parser_process()


if __name__ == "__main__":

    main()
'''