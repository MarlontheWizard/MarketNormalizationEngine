import os
import requests
from zipfile import ZipFile
from io import BytesIO
import argparse
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "bi5_data")

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


def download_file(url):
    
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        print("[ERROR] URL unreachable.")
        return None
    
    return r.content


def extract_zip(zip_bytes, output_dir):
    with ZipFile(BytesIO(zip_bytes)) as z:
        z.extractall(output_dir)


def download_day(symbol, year, month, day, output_dir="bi5_data"):

    for hour in range(0, 24, 1):     
        
        url = build_download_url(symbol, year, month, day, hour)
        print(f"[INFO] Downloading: {url}")
        data = download_file(url)
        
        if data is None:
            
            print("[WARNING] No data for this date.")
            
            continue

        dir = os.path.join(
            output_dir,
            symbol,
            f"{year}-{month:02d}-{day:02d}"
        )

        os.makedirs(dir, exist_ok=True)

        file_name = build_filename(symbol, year, month, day, hour)
        
        open(file, "wb").write(data)

    #extract_zip(data, dir)

    print(f"[SUCCESSFUL] Fetched data saved to {dir}")


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

    return parser.parse_args()


if __name__ == "__main__":
    
    args = parse_args()

    #Single day mode
    if args.year and args.month and args.day:

        download_day(
            symbol=args.symbol,
            year=args.year,
            month=args.month,
            day=args.day
        )

    #Range mode
    elif args.start_date and args.end_date:
        
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")

        current_date = start_date

        while current_date <= end_date:
            
            download_day(
                symbol=args.symbol,
                year=current_date.year,
                month=current_date.month,
                day=current_date.day
            )

            current_date += timedelta(days=1)

    else:
        
        print("[ERROR] Provide either --date or both --start-date and --end-date")