import os
import requests
from zipfile import ZipFile
from io import BytesIO
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import lzma
import argparse
import time


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

    #dukascopy uses zero based month values
    dukascopy_month = month - 1 

    return(
    f"{BASE_URL}/"
    f"{symbol.upper()}/"
    f"{year}/"
    f"{dukascopy_month:02d}/"
    f"{day:02d}/"
    f"{hour:02d}h_ticks.bi5"
    )


def log_download(symbol, year, month, day, hour, message):

    tqdm.write(f"[{symbol} {year}-{month:02d}-{day:02d} {hour:02d}h] {message}")
    

def fetch_data_from_server(symbol, year, month, day, hour, url, retries=5, timeout=350, backoff_base=2):

    for attempt in range(1, retries + 1):

        
        try:

            r = requests.get(url, timeout=timeout)

            if r.status_code == 404:

    		return None, "missing_hour_404"

            if r.status_code != 200:

               log_download(symbol, year, month, day, hour,

                f"FETCH WARNING HTTP {r.status_code} attempt {attempt}/{retries}")

            
            elif not r.content:

                return None, "empty_response"

            
            else:

                return r.content, None

        
        except requests.exceptions.RequestException as e:

            log_download(symbol, year, month, day, hour,

                f"FETCH RETRY attempt {attempt}/{retries} error={e}")

        
        if attempt < retries:

            sleep_time = backoff_base ** (attempt - 1)

            log_download(symbol, year, month, day, hour,

                f"BACKOFF sleeping {sleep_time}s before retry")

            
            time.sleep(sleep_time)

    
    log_download(symbol, year, month, day, hour, "FETCH FAILED")
    
    return None, "fetch_failed"

    


def is_valid_bi5(data: bytes) -> bool:

    try:

        lzma.decompress(data)

        return True

    except Exception:

        return False



def download_hour_data(symbol, year, month, day, hour, output_dir):

    url = build_download_url(symbol, year, month, day, hour)

    data, fetch_reason = fetch_data_from_server(symbol, year, month, day, hour, url)

    
    if data is None:

        return {"success": False, "hour": hour, "reason": fetch_reason}

    
    if not is_valid_bi5(data):

        return {"success": False, "hour": hour, "reason": "no_valid_ticks_or_corrupted"}

    
    file_name = build_filename(symbol, year, month, day, hour)

    file_path = os.path.join(output_dir, file_name)

    
    with open(file_path, "wb") as f:

        f.write(data)

    
    return {"success": True, "hour": hour, "reason": None}

    #print(f"[SUCCESSFUL] Completed hour {hour}. Fetched data saved to {dir}")

    
#Dukascopy server only provides data in hourly timeframe
def download_day_data(symbol, year, month, day, output_dir):

    hours = list(range(24))

    failed_hours = []

    skipped_hours = []

    retryable_reasons = {"fetch_failed"}

    
    with ThreadPoolExecutor(max_workers=4) as executor:

        futures = [

            executor.submit(download_hour_data, symbol, year, month, day, hour, output_dir) 

            for hour in hours

        ]

        with tqdm(total=len(futures), desc=f"{symbol} {year}-{month:02d}-{day:02d}") as pbar:

            for future in as_completed(futures):

                result = future.result()

                if not result["success"]:

                    if result["reason"] in retryable_reasons:

                        failed_hours.append(result["hour"])

                    else:

                        skipped_hours.append((result["hour"], result["reason"]))

                pbar.update(1)

    
    if skipped_hours:

        tqdm.write("[SKIPPED HOURS]")

        for hour, reason in sorted(skipped_hours):

            tqdm.write(f"  {symbol} {year}-{month:02d}-{day:02d} " f"{hour:02d}h -> {reason}")

    
    if failed_hours:

        tqdm.write(f"[RETRY QUEUE] Retrying failed hours: {failed_hours}")

        retry_failed_hours = []

        for hour in failed_hours:

            result = download_hour_data(symbol, year, month, day, hour, output_dir)

            
            if not result["success"]:

                retry_failed_hours.append(hour)

                tqdm.write(f"[FINAL ATTEMPT FAILED] "f"{symbol} {year}-{month:02d}-{day:02d} "f"{hour:02d}h reason={result['reason']}")

            
            else:

                tqdm.write(f"[RECOVERED] "f"{symbol} {year}-{month:02d}-{day:02d} "f"{hour:02d}h")

        
        if retry_failed_hours:

            tqdm.write(f"[WARNING] Unresolved missing hours: {retry_failed_hours}")
   
    #print(f"[DONE] Completed {year}-{month:02d}-{day:02d}")



def process_download(symbol, year, month, day, output_dir):

    download_day_data(symbol, year, month, day, output_dir)



def begin_downloader_process(symbol, start_date, end_date=None, location = "raw_data"):
    
    
    print("[DOWNLOADER START] Beginning download(s) for requested data from Dukascopy...")

    parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d")

    if end_date is None: #Single day mode

        output_dir = os.path.join(
            location,
            symbol,
            f"{parsed_start_date.year}-{parsed_start_date.month:02d}-{parsed_start_date.day:02d}"
        )

        os.makedirs(output_dir, exist_ok=True)
    
        process_download(
            symbol=symbol,
            year=parsed_start_date.year,
            month=parsed_start_date.month,
            day=parsed_start_date.day,
            output_dir=output_dir,
        )
            
    elif end_date is not None: #Range mode
        
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

        current_date = parsed_start_date

        while current_date <= end_date:

            parsed_current_date = current_date

            output_dir = os.path.join(
                location,
                symbol,
                f"{parsed_current_date.year}-{parsed_current_date.month:02d}-{parsed_current_date.day:02d}"
            )

            os.makedirs(output_dir, exist_ok=True)
    
            process_download(
                symbol=symbol,
                year=parsed_current_date.year,
                month=parsed_current_date.month,
                day=parsed_current_date.day,
                output_dir=output_dir,
            )

            current_date += timedelta(days=1)
            
    else:
        
        print("[DOWNLOADER ERROR] Provide either --date or both --start-date and --end-date")

        return 

    print(f"[DOWNLOADER END] Fetched data successfully saved to directory named {location}.")   



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
