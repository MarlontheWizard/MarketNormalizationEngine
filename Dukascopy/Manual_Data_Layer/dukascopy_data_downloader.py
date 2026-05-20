import os
import requests
from zipfile import ZipFile
from io import BytesIO
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import lzma
import argparse


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#Server location
BASE_URL = "https://datafeed.dukascopy.com/datafeed"

def build_filename(symbol: str,
                   year: int,
                   month: int,
                   day: int,
                   hour: int) -> str:
    
    return f"{symbol.upper()}_{year}{month:02d}{day:02d}_{hour:02d}h.bi5"


#Builds url for fetching data from Dukascopy server for download
def build_download_url(symbol: str, 
              year: int, 
              month: int, 
              day: int,
              hour: str = "") -> str:


    return(
    f"{BASE_URL}/"
    f"{symbol.upper()}/"
    f"{year}/"
    f"{month:02d}/"
    f"{day:02d}/"
    f"{hour:02d}h_ticks.bi5"
    )


def fetch_data_from_server(url):
    
    r = requests.get(url, timeout=350)    
    
    if r.status_code != 200:
        print("[ERROR] URL unreachable.")
        return None
    
    return r.content


def download_hour_data(symbol, year, month, day, hour, output_dir):
 
        
    url = build_download_url(symbol, year, month, day, hour)
    
    #print(f"[INFO] Downloading: {url}")
    
    data = fetch_data_from_server(url)
        
    if data is None:
            
        print(f"[WARNING] No data for hour {hour} on {year}-{month}-{day}")    

        return

    #Validate LZMA integrity before saving
    try:
        
        lzma.decompress(data)

    except Exception:

        print(f"[CORRUPTED DOWNLOAD] {url}")

        return


    file_name = build_filename(symbol, year, month, day, hour)

    file_path = os.path.join(output_dir, file_name)
    
    with open(file_path, "wb") as f:
        
        f.write(data)

    #print(f"[SUCCESSFUL] Completed hour {hour}. Fetched data saved to {dir}")

    
#Dukascopy server only provides data in hourly timeframe
def download_day_data(symbol, year, month, day, output_dir, threads=4):

    hours = list(range(24))

    with ThreadPoolExecutor(max_workers=threads) as executor:

        futures = [
            executor.submit(
                download_hour_data,
                symbol,
                year,
                month,
                day,
                hour,
                output_dir
            )
            
            for hour in hours
        ]

        results = []

        with tqdm(total=24, desc=f"{symbol} {year}-{month:02d}-{day:02d}") as pbar:

            for f in as_completed(futures):
                f.result()
                pbar.update(1)
                
    #print(f"[DONE] Completed {year}-{month:02d}-{day:02d}")


def process_download(symbol, year, month, day, output_dir, threads):

    download_day_data(symbol, year, month, day, output_dir, threads)


#Comment this function out to faciliate direct isolated testing
def begin_downloader_process(args):
    
    print("[DOWNLOADER START] Beginning download(s) for requested data from Dukascopy...")
    
    #Single day mode
    if args.year and args.month and args.day:

        output_dir = os.path.join(
                args.location,
                args.symbol,
                f"{args.year}-{args.month:02d}-{args.day:02d}"
            )

        os.makedirs(output_dir, exist_ok=True)
    
        process_download(
            symbol=args.symbol,
            year=args.year,
            month=args.month,
            day=args.day,
            output_dir=output_dir,
            threads=args.threads
        )

    #Range mode
    elif args.start_date and args.end_date:
        
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")

        current_date = start_date

        while current_date <= end_date:

            output_dir = os.path.join(
                args.location,
                symbol,
                f"{year}-{month:02d}-{day:02d}"
            )

            os.makedirs(output_dir, exist_ok=True)
    
            process_download(
                symbol=args.symbol,
                year=current_date.year,
                month=current_date.month,
                day=current_date.day,
                output_dir=output_dir,
                threads=args.threads
            )

            current_date += timedelta(days=1)
            
    else:
        
        print("[DOWNLOADER ERROR] Provide either --date or both --start-date and --end-date")

        return 

    print(f"[DOWNLOADER END] Fetched data successfully saved to directory named {args.location}.")   



''' Uncomment to facilitate direct isolated testing
def parse_args():
    
    parser = argparse.ArgumentParser(description="Dukascopy Data Downloader")

    parser.add_argument("--symbol", type=str, default="EURUSD", help="Market symbol (e.g. EURUSD)")

    #Single day
    parser.add_argument("--year", type=int, help="Year")
    parser.add_argument("--month", type=int, help="Month")
    parser.add_argument("--day", type=int, help="Day") 

    #Range
    parser.add_argument("--start-date", type=str, help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end-date", type=str, help="End date in YYYY-MM-DD format")

    #Threads
    parser.add_argument(
        "--threads",
        type=int,
        default=4,
        help="Number of parallel download threads to use"
    )

    #Folder name
    parser.add_argument(
        "--location",
        type=str,
        default="bi5_data",
        help="Specify directory/location to store data in"
    )
    
    return parser.parse_args()


def main():
    
    args = parse_args()

    print("[BEGIN] Download requested data from Dukascopy.")
          
    #Single day mode
    if args.year and args.month and args.day:

        output_dir = os.path.join(
                args.location,
                args.symbol,
                f"{args.year}-{args.month:02d}-{args.day:02d}"
            )

        os.makedirs(output_dir, exist_ok=True)
    
        process_download(
            symbol=args.symbol,
            year=args.year,
            month=args.month,
            day=args.day,
            output_dir=output_dir,
            threads=args.threads
        )

    #Range mode
    elif args.start_date and args.end_date:
        
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")

        current_date = start_date

        while current_date <= end_date:

            output_dir = os.path.join(
                args.location,
                symbol,
                f"{year}-{month:02d}-{day:02d}"
            )

            os.makedirs(output_dir, exist_ok=True)
    
            process_download(
                symbol=args.symbol,
                year=current_date.year,
                month=current_date.month,
                day=current_date.day,
                output_dir=output_dir,
                threads=args.threads
            )

            current_date += timedelta(days=1)
            
    else:
        
        print("[ERROR] Provide either --date or both --start-date and --end-date")

        return 

    print(f"[END] Fetched data saved to directory named {args.location}.")


if __name__ == "__main__":
    main()

'''