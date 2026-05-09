import os
import requests
from zipfile import ZipFile
from io import BytesIO
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "bi5_data")

BASE_URL = "https://datafeed.dukascopy.com/datafeed"

#Constructs Dukascopy dataset filename part - Example: BID_candles_min_1
def build_dataset_name(price_type: str = "BID", data_type: str = "candles", timeframe: str = "min_1") -> str:
    
    return f"{price_type.upper()}_{data_type}_{timeframe}"


#Builds url (uses default values in case arguments are not provided) for download
def build_url(symbol: str, 
              year: int, 
              month: int, 
              day: int,
              price_type: str = "BID",
              data_type: str = "candles",
              timeframe: str = "min_1") -> str:

    zip_file_name = build_dataset_name(price_type, data_type, timeframe)

    return (
    f"{BASE_URL}/"
    f"{symbol.upper()}/"
    f"{year}/"
    f"{month:02d}/"
    f"{day:02d}/"
    f"00h_ticks.bi5"
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


def download_day(symbol, year, month, day, output_dir="OUTPUT_DIR"):
    url = build_url(symbol, year, month, day)

    print(f"[INFO] Downloading: {url}")

    data = download_file(url)

    if data is None:
        print("[WARNING] No data for this date.")
        return

    dir = os.path.join(
        output_dir,
        symbol,
        f"{year}-{month:02d}-{day:02d}"
    )

    os.makedirs(dir, exist_ok=True)

    #extract_zip(data, dir)

    print(f"[SUCCESSFUL] Data saved to {dir}")


def parse_args():
    parser = argparse.ArgumentParser(description="Dukascopy Data Downloader")

    parser.add_argument("--symbol", type=str, default="EURUSD", help="Market symbol (e.g. EURUSD)")
    parser.add_argument("--year", type=int, default=2024, help="Year")
    parser.add_argument("--month", type=int, default=1, help="Month")
    parser.add_argument("--day", type=int, default=2, help="Day")
    parser.add_argument("--output", type=str, default="data", help="Output directory")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    #TODO: Change single date specification to range 
    download_day(
        symbol=args.symbol,
        year=args.year,
        month=args.month,
        day=args.day,
        output_dir=args.output
    )