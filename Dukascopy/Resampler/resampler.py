import pandas as pd
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


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

    tqdm.write(f"[RESAMPLER SAVED] {output_path}")

    resampled.to_parquet(output_path)


def group_files_by_day(parquet_dir):

    grouped_files = {}

    
    if not os.path.exists(parquet_dir):

        tqdm.write(f"[RESAMPLER ERROR] Directory does not exist: {parquet_dir}")

        return grouped_files

        
    for root, _, files in os.walk(parquet_dir):

        for file in files:

            if not file.endswith(".parquet"):
                continue

            full_path = os.path.join(root, file)

            
            try:

                date = file.split("_")[1][:8]

            except IndexError:

                tqdm.write(f"[RESAMPLER WARNING] Skipping invalid filename: {file}")

                continue

                
            grouped_files.setdefault(date, []).append(full_path)
            

    if not grouped_files:

        tqdm.write(f"[RESAMPLER WARNING] No parquet files found in: {parquet_dir}")
        
    return grouped_files


def load_day_files(files):

    if not files:

        return pd.DataFrame()

    dataframes = []

    for file in sorted(files):

        try:

            df = pd.read_parquet(file)

            if df.empty:

                tqdm.write(f"[RESAMPLER WARNING] Empty parquet file skipped: {file}")

                continue

            dataframes.append(df)

        
        except Exception as e:

            tqdm.write(f"[RESAMPLER ERROR] Failed to read {file}: {e}")

    
    if not dataframes:

        return pd.DataFrame()

    
    combined_df = pd.concat(dataframes, ignore_index=True)

    
    if "timestamp" not in combined_df.columns:

        tqdm.write("[RESAMPLER ERROR] Missing timestamp column.")

        return pd.DataFrame()

    
    combined_df["timestamp"] = pd.to_datetime(combined_df["timestamp"])

    combined_df = combined_df.sort_values("timestamp")

    return combined_df.reset_index(drop=True)



def resample_ticks(df: pd.DataFrame, timeframe: str = "1min") -> pd.DataFrame:
    
    '''
    Resample tick data into OHLCV-style bars.

    Parameters:
        df (pd.DataFrame): tick data with timestamp, bid, ask, volumes
        timeframe (str): pandas offset alias (e.g. '1min', '5min', '1H')

    Returns:
        pd.DataFrame: resampled OHLCV dataframe
    '''

    if df is None or df.empty:

        return pd.DataFrame()

    
    required_columns = {"timestamp", "bid", "ask", "bid_volume", "ask_volume"}

    missing_columns = required_columns - set(df.columns)

    
    if missing_columns:

        tqdm.write(f"[RESAMPLER ERROR] Missing required columns: {missing_columns}")

        return pd.DataFrame()

        
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



def process_day(date, files, symbol, timeframe, output_base):

    try:

        df = load_day_files(files)

        if df.empty:

            return {"success": False, "date": date, "reason": "no_data_loaded"}

        
        resampled = resample_ticks(df, timeframe)

        if resampled.empty:

            return {"success": False, "date": date, "reason": "no_resampled_data"}

        
        save_resampled_data(resampled, symbol=symbol, timeframe=timeframe, date=date, output_base=output_base)

        return {"success": True, "date": date, "rows": len(resampled), "dataframe": resampled}

    
    except Exception as e:

        return {"success": False, "date": date, "reason": str(e)}
    


    
def invoke_resampler(parquet_dir: str, symbol: str, timeframe: str, output_base="resampled_data", return_combined=False):


    tqdm.write(f"[RESAMPLER START] Resampling {symbol} from {parquet_dir} " f"to timeframe = {timeframe}")

    
    grouped = group_files_by_day(parquet_dir)

    
    if not grouped:

        tqdm.write("[RESAMPLER END] No data available to resample.")

        return {}

        
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

        with tqdm(total=len(futures), desc="Resampling") as pbar:

            for future in as_completed(futures):

                result = future.result()

                if result["success"]:

                    tqdm.write(f"[RESAMPLER SUCCESS] {result['date']} " f"rows={result['rows']}")

                    results[result["date"]] = result["dataframe"]
                    
                else:

                    tqdm.write(f"[RESAMPLER SKIPPED] {result['date']} " f"reason={result['reason']}")

                
                pbar.update(1)

    
    tqdm.write(f"[RESAMPLER END] Completed. Successful days: {len(results)}\n")

    
    if return_combined:
        
        if not results:

            return pd.DataFrame()

            
        return (pd.concat(results.values(), ignore_index=True).sort_values("timestamp").reset_index(drop=True))


    return results
    



    
''' Uncomment to facilitate direct isolated testing 
def main():

    invoke_resampler()
    
    

if __name__ == "__main__":

    main()
'''