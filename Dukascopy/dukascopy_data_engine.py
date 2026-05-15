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

    #Folder name
    parser.add_argument(
        "--location",
        type=str,
        default="bi5_data",
        help="Specify directory/location to store data in"
    )
    
    return parser


def build_cli_parser():

    cli_parser = argparse.ArgumentParser(description="MarketNormalizationEngine")

    subparsers = cli_parser.add_subparsers(dest="command")

    downloader_parser = cli_downloader_args()

    parse_parser = cli_parser_args()


def process_cli_parser():

    cli_parser = build_cli_parser()

    args = cli_parser.parse_args()

    if args.command == "fetch":
        
        begin_downloader_process(args)

    elif args.command == "parse":

        
        pass
        
        #(args)

    else:
        
        cli_parser.print_help()

    
def main():

    process_cli_parser()



if __name__ == "__main__":
    
    main()