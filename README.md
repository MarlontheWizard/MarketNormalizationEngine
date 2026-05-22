# MarketNormalizationEngine

Author Note: Please star this repository if you find it useful! It means alot to me.
             Email marlon.dominguez307@gmail.com for any implementation requests, contribution requests, or bugs.  

### Overview

A high-performance, parallelized market data ingestion tool designed to download and structure raw tick data from Dukascopy into a clean, ML-ready format.

This project focuses on data normalization infrastructure, not trading logic.

## Dukascopy (Forex Data)

### Architecture

The system is designed around a clean separation of concerns:

- Downloader → fetch raw `.bi5` tick data
- Storage Layer → organize files by symbol/date/hour
- Parser → decode bid/ask/mid and normalie
- Resampler → Produce dataframe with requested timeframe

### Features

- Parallel downloads using ThreadPoolExecutor
- Clean hierarchical storage structure
- Hour-based tick segmentation
- Code and/or CLI-driven execution 
- Resampler to provide data as dataframe for usage in code 

### CLI Usage

NOTE: Resampler cannot be used through CLI. Read the next section to learn more.

As mentioned below, if a specific operation is not specified then the downloader and parser are both performed.

#### Single Day Download

```bash
python dukascopy_data_engine.py --symbol EURUSD --year 2024 --month 1 --day 2
```

#### Range Download

```bash
python dukascopy_data_engine.py --symbol EURUSD --start-date 2024-01-01 --end-date 2024-01-10
```

#### Default Operation Control

NOTE: If fetch or parse are not specified in the command line then both are performed.

To specify an operation insert fetch or parse:

```bash
python dukascopy_data_engine.py <operation> --symbol EURUSD --year 2024 --month 1 --day 2
```

#### Default Thread Behavior

The downloader and parser use four threads.

#### Custom Thread Behavior

Custom thread behavior has been removed. If you would like a different thread count then you must change it in the code.

#### Data Target Location

##### Specify Directory

To specify the location to place the data in use:

```bash
--location {location}
```

If not specified then data is stored in engine directory.

###Code Usage

If using in code then you must invoke both the downloader, parser and of course the resampler individually. 

#### Import

Import dukascopy_bi5_data_parser, dukascopy_data_downloader, and resampler in your code as needed. 

#### Using the downloader

Invoke the following function:

```bash
def begin_downloader_process(symbol, start_date, end_date=None, location = "raw_data")
```

Example: 

```bash
from dukascopy_data_downloader import begin_downloader_process

begin_downloader_process(
    symbol="EURUSD",
    start_date="2024-01-02",
    end_date=None,
    location="raw_data"
)
```

####Using the Parser

Invoke the following function:

Example:

```bash
from dukascopy_bi5_data_parser import begin_parser_process 

begin_parser_process(
    	"bi5_data",
    	"parsed_data"
)
```

####Using the Resampler

Example: 

```bash
import resampler
import pandas as pd

df = resampler.invoke_resampler("../Manual_Data_Layer/parsed_data", "1d")
```
