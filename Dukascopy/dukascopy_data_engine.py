from Manual_Data_Layer import dukascopy_bi5_data_parser
from Manual_Data_Layer import dukascopy_data_downloader
import os
import argparse
import sys


def cli_parser_args():

    parser = subparsers.add_parser("parse")

    parser.add_argument("--input", type=str, help="Location of data to parse", default="bi5_data")

    return parser
    
    
def cli_downloader_args():
    
    parser = subparsers.add_parser("download")

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

    #Folder name(s)
    parser.add_argument(
        "--raw-data-dir",
        type=str,
        default="raw_data",
        help="Specify directory/location to store server data in"
    )

    parser.add_argument(
        "--parsed-data-dir",
        type=str,
        default="parsed_data",
        help="Specify directory/location to store parsed data in"
    )

    
    
    return parser


def build_cli_parser():

    cli_parser = argparse.ArgumentParser(description="MarketNormalizationEngine")

    subparsers = cli_parser.add_subparsers(dest="command")

    downloader_parser = cli_downloader_args()

    parse_parser = cli_parser_args()


def process_cli():

    cli_parser = build_cli_parser()

    args = cli_parser.parse_args()

    if args.command == "fetch":
        
        begin_downloader_process(args)

    elif args.command == "parse":

        begin_parser_process(args):

    else: #do both
        
        try:
            
            begin_downloader_process(args)


        except Exception as e:

            print(f"[ENGINE ERROR] An error occurred: {e}")
            
            cli_parser.print_help()


def print_banner():
    
    print("""
╔════════════════════════════════════════════════════════════╗
║            DUKASCOPY DATA NORMALIZATION ENGINE             ║
╠════════════════════════════════════════════════════════════╣
║  Pipeline : BI5 → Tick Parser → Parquet Conversion         ║
║                                                            ║
║  Author   : Marlon Dominguez                               ║
║  GitHub   : https://github.com/MarlontheWizard             ║
║                                                            ║
║  Status   : Initializing engine...                         ║
╚════════════════════════════════════════════════════════════╝
""")


def start_dukascopy_engine():

    print_banner()
    process_cli()


def main():

    start_dukascopy_engine()
    

if __name__ == "__main__":
    
    main()