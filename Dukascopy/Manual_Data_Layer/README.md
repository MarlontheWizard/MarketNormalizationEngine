# MarketNormalizationEngine

## Overview

A high-performance, parallelized market data ingestion tool designed to download and structure raw tick data from Dukascopy into a clean, ML-ready format.

This project focuses on data normalization infrastructure, not trading logic.

## Architecture

The system is designed around a clean separation of concerns:

- Downloader → fetch raw `.bi5` tick data
- Storage Layer → organize files by symbol/date/hour
- Parser → decode bid/ask/mid and normaliz

## Features

- Parallel downloads using ThreadPoolExecutor
- Clean hierarchical storage structure
- Hour-based tick segmentation
- CLI-driven execution

## CLI Usage

### Single Day Download

```bash
python dukascopy_data_downloader.py --symbol EURUSD --year 2024 --month 1 --day 2

### Range Download

```bash
python dukascopy_data_downloader.py \
  --symbol EURUSD \
  --start-date 2024-01-01 \
  --end-date 2024-01-10

## Thread Control

The downloader supports configurable parallelism using threads.

### Default Behavior

If no thread count is specified, the downloader uses:

```bash
--threads 4

### Custom Behavior
python dukascopy_data_downloader.py \
  --symbol EURUSD \
  --year 2024 \
  --month 1 \
  --day 2 \
  --threads 12

### Disable Parallel Downloads

For single thread behavior use:

```bash
--threads 1

## Data Target Location

### Specify Directory

To specify the location (created if doesn't exist) to place the data in use:

```bash
--location {location}

The default location is bi5_data in current directory.

