import pandas as pd
import os

def load_parquet_files(parquet_dir: str) -> pd.DataFrame:

    parquet_files = []

    #recursively find parquet files
    for root, _, files in os.walk(parquet_dir):

        for file in files:

            if file.endswith(".parquet"):

                parquet_files.append(
                    os.path.join(root, file)
                )

    parquet_files = sorted(parquet_files)

    if not parquet_files:

        raise FileNotFoundError(
            f"No parquet files found in: {parquet_dir}"
        )

    #load all parquet files
    dataframes = [
        pd.read_parquet(file)
        for file in parquet_files
    ]

    #combine into single dataframe
    combined_df = pd.concat(
        dataframes,
        ignore_index=True
    )

    #ensure timestamps are datetime
    combined_df["timestamp"] = pd.to_datetime(
        combined_df["timestamp"]
    )

    #sort chronologically
    combined_df = combined_df.sort_values(
        "timestamp"
    )

    #reset clean index
    combined_df = combined_df.reset_index(drop=True)

    return combined_df



def resample_ticks(df: pd.DataFrame, timeframe: str = "1min") -> pd.DataFrame:
    """
    Resample tick data into OHLCV-style bars.

    Parameters:
        df (pd.DataFrame): tick data with timestamp, bid, ask, volumes
        timeframe (str): pandas offset alias (e.g. '1min', '5min', '1H')

    Returns:
        pd.DataFrame: resampled OHLCV dataframe
    """

    df = df.copy()

    #ensure datetime index
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
    #optional: spread feature
    df["spread"] = df["ask"] - df["bid"]
    resampled["avg_spread"] = df["spread"].resample(timeframe).mean()
    '''
    
    #clean up
    resampled = resampled.dropna().reset_index()

    return resampled


def invoke_resampler(parquet_dir: str, timeframe: str):

    return resample_ticks(load_parquet_files(parquet_dir), timeframe)


#''' Uncomment to facilitate direct isolated testing 
def main():

    invoke_resampler()
    
    

if __name__ == "__main__":

    main()
#'''