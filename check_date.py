import pandas as pd
import argparse
import os
import sys

def check_file_integrity(filepath, start_date=None, end_date=None):
    if not os.path.exists(filepath):
        path_in_subdir = os.path.join("csv files", filepath)
        if os.path.exists(path_in_subdir):
            filepath = path_in_subdir
        else:
            print(f"Error: File not found: {filepath}")
            return

    print(f"\n=========================================================================")
    print(f"               DATA INTEGRITY & TIMEFRAME AUDIT REPORT                  ")
    print(f"=========================================================================")
    print(f" File: {filepath}")
    
    try:
        df = pd.read_csv(filepath, sep=None, engine='python')
        if len(df.columns) == 6:
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            
        date_col = [c for c in df.columns if 'date' in c.lower()][0]
        df[date_col] = pd.to_datetime(df[date_col], format='mixed')
        df.set_index(date_col, inplace=True)
        df.sort_index(inplace=True)

        total_rows = len(df)
        start_ts = df.index.min()
        end_ts = df.index.max()
        duration = end_ts - start_ts

        print(f" Start Timestamp:   {start_ts}")
        print(f" End Timestamp:     {end_ts}")
        print(f" Total Duration:    {duration}")
        print(f" Total Data Bars:   {total_rows}")

        # Data Quality Checks
        null_counts = df[['open', 'high', 'low', 'close']].isnull().sum().sum()
        zero_counts = (df[['open', 'high', 'low', 'close']] <= 0).sum().sum()
        duplicates = df.index.duplicated().sum()

        print("-------------------------------------------------------------------------")
        print(" DATA INTEGRITY METRICS:")
        print(f"  - Missing/NaN Values: {null_counts} {'[OK]' if null_counts == 0 else '[WARNING]'}")
        print(f"  - Zero/Negative Prices: {zero_counts} {'[OK]' if zero_counts == 0 else '[WARNING]'}")
        print(f"  - Duplicate Timestamps: {duplicates} {'[OK]' if duplicates == 0 else '[WARNING]'}")

        # Optional Date Range Filtering
        if start_date or end_date:
            filtered_df = df.copy()
            if start_date:
                filtered_df = filtered_df[filtered_df.index >= pd.to_datetime(start_date)]
            if end_date:
                filtered_df = filtered_df[filtered_df.index <= pd.to_datetime(end_date)]
            print("-------------------------------------------------------------------------")
            print(f" FILTERED DATE RANGE ({start_date or 'Start'} to {end_date or 'End'}):")
            print(f"  - Filtered Bar Count: {len(filtered_df)}")
            print(f"  - Coverage: {(len(filtered_df) / total_rows) * 100:.2f}% of full dataset")

        print("=========================================================================\n")

    except Exception as e:
        print(f"Error auditing file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CSV Data Integrity & Timestamp Auditor")
    parser.add_argument("file", type=str, nargs="?", default="XAUUSD_M5.csv", help="Target CSV file name")
    parser.add_argument("--start-date", type=str, default=None, help="Filter dataset from start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default=None, help="Filter dataset up to end date (YYYY-MM-DD)")
    args = parser.parse_args()

    check_file_integrity(args.file, start_date=args.start_date, end_date=args.end_date)
