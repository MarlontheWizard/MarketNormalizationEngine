import pandas as pd
import os
from concurrent.futures import ThreadPoolExecutor


def save_resampled_data(resampled, symbol, timeframe, date, output_base="resampled_data"):

    output_dir = os.path.join(
        output_base,
        symbol,
        timeframe
    )

    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(
        output_dir,
        f"{date}.parquet"
    )
    
    resampled.to_parquet(output_path)


def group_files_by_day(parquet_dir):

    grouped_files = {}

    for root, _, files in os.walk(parquet_dir):

        for file in files:

            if not file.endswith(".parquet"):
                continue

            full_path = os.path.join(root, file)

            date = file.split("_")[1][:8]

            if date not in grouped_files:

                grouped_files[date] = []

            grouped_files[date].append(full_path)

    return grouped_files


def load_day_files(files):

    dataframes = [
        pd.read_parquet(file)
        for file in sorted(files)
    ]

    combined_df = pd.concat(
        dataframes,
        ignore_index=True
    )

    combined_df["timestamp"] = pd.to_datetime(
        combined_df["timestamp"]
    )

    combined_df = combined_df.sort_values(
        "timestamp"
    )

    return combined_df.reset_index(drop=True)



def process_day(date, files, symbol, timeframe, output_base):

    df = load_day_files(files)

    resampled = resample_ticks(df, timeframe)

    save_resampled_data(resampled, symbol=symbol, timeframe=timeframe, date=date, output_base=output_base)

    return resampled
    
    
def resample_ticks(df: pd.DataFrame, timeframe: str = "1min") -> pd.DataFrame:
    
    '''
    Resample tick data into OHLCV-style bars.

    Parameters:
        df (pd.DataFrame): tick data with timestamp, bid, ask, volumes
        timeframe (str): pandas offset alias (e.g. '1min', '5min', '1H')

    Returns:
        pd.DataFrame: resampled OHLCV dataframe
    '''

    df = df.copy()

    #datetime index
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp")

    #mid price is more stable than raw bid/ask
    df["mid"] = (df["bid"] + df["ask"]) / 2

    #aggregate rules
    resampled = pd.DataFrame()

    resampled["open"] = df["mid"].resample(timeframe).first()
    resampled["high"] = df["mid"].resample(timeframe).max()
    resampled["low"] = df["mid"].resample(timeframe).min()
    resampled["close"] = df["mid"].resample(timeframe).last()

    #volume aggregation
    resampled["bid_volume"] = df["bid_volume"].resample(timeframe).sum()
    resampled["ask_volume"] = df["ask_volume"].resample(timeframe).sum()

    '''
    #optional spread feature
    df["spread"] = df["ask"] - df["bid"]
    resampled["avg_spread"] = df["spread"].resample(timeframe).mean()
    '''

    resampled = resampled.dropna().reset_index()
        
    return resampled


    
def invoke_resampler(parquet_dir: str, symbol: str, timeframe: str, output_base="resampled_data"):

    grouped = group_files_by_day(parquet_dir)

    results = {}

    with ThreadPoolExecutor(max_workers=4) as executor:

        futures = [
            executor.submit(
                process_day,
                date,
                files,
                symbol,
                timeframe,
                output_base
            )
            for date, files in grouped.items()
        ]

        for f in futures:
            df = f.result()
            results[df["timestamp"].iloc[0].date()] = df

    return results
    

    
''' Uncomment to facilitate direct isolated testing 
def main():

    invoke_resampler()
    
    

if __name__ == "__main__":

    main()
'''