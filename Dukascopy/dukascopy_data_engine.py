from Manual_Data_Layer import dukascopy_bi5_data_parser
from Manual_Data_Layer import dukascopy_data_downloader
from Resampler import resampler

import os
import argparse
import sys



def cli_resampler_args(parser):
    
    parser.add_argument("--timeframe", type=str, help="specify desired timeframe to resample")

    parser.add_argument("--resampled-data-dir", type=str, default="resampled_data", help="specify location to place resampled data in")

    return parser

    
    
def cli_common_args(parser):


    #Operation
    parser.add_argument("--operation", type=str, help="resample is the only operation available")
    
    #Symbol(s)
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
        "----raw-data-dir",
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

    parser = argparse.ArgumentParser(description="MarketNormalizationEngine")

    cli_common_args(parser)

    cli_resampler_args(parser)

    return parser



def print_resampler_banner():
    
    print("""
╔════════════════════════════════════════════════════════════╗
║            DUKASCOPY DATA NORMALIZATION ENGINE             ║
╠════════════════════════════════════════════════════════════╣
║  Pipeline : BI5 → Tick Parser → Parquet Conversion         ║
║                                                            ║
║  Author   : Marlon Dominguez                               ║
║  GitHub   : https://github.com/MarlontheWizard             ║
║                                                            ║
║  Status   : Invoking resampler...                          ║
╚════════════════════════════════════════════════════════════╝
""")

    
def print_default_banner():
    
    print("""
╔════════════════════════════════════════════════════════════╗
║            DUKASCOPY DATA NORMALIZATION ENGINE             ║
╠════════════════════════════════════════════════════════════╣
║  Pipeline : BI5 → Tick Parser → Parquet Conversion         ║
║                                                            ║
║  Author   : Marlon Dominguez                               ║
║  GitHub   : https://github.com/MarlontheWizard             ║
║                                                            ║
║  Status   : Invoking downloader and parser...              ║
╚════════════════════════════════════════════════════════════╝
""")

    

def process_cli():

    cli_parser = build_cli_parser()
    
    args = cli_parser.parse_args()

    try:

        if args.operation == "resample":

            print_resampler_banner()

            resampler.invoke_resampler(args.parsed_data_dir, args.symbol, args.timeframe, args.resampled_data_dir)
            
        else:

            print_default_banner()
        
            dukascopy_data_downloader.begin_downloader_process(args.symbol, args.start_date, args.end_date, args.raw_data_dir)
            dukascopy_bi5_data_parser.begin_parser_process(args.raw_data_dir, args.parsed_data_dir)

        
    except Exception as e:

        print(f"[ENGINE ERROR] An error occurred: {e}")
            
        cli_parser.print_help()


def start_dukascopy_engine():

    process_cli()


def main():

    start_dukascopy_engine()
    

if __name__ == "__main__":
    
    main()