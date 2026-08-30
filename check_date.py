import pandas as pd
import argparse
import os
import sys
import json

def check_file_integrity(filepath, start_date=None, end_date=None, export_json=None):
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
        null_counts = int(df[['open', 'high', 'low', 'close']].isnull().sum().sum())
        zero_counts = int((df[['open', 'high', 'low', 'close']] <= 0).sum().sum())
        duplicates = int(df.index.duplicated().sum())

        print("-------------------------------------------------------------------------")
        print(" DATA INTEGRITY METRICS:")
        print(f"  - Missing/NaN Values: {null_counts} {'[OK]' if null_counts == 0 else '[WARNING]'}")
        print(f"  - Zero/Negative Prices: {zero_counts} {'[OK]' if zero_counts == 0 else '[WARNING]'}")
        print(f"  - Duplicate Timestamps: {duplicates} {'[OK]' if duplicates == 0 else '[WARNING]'}")

        summary = {
            "file": filepath,
            "start_timestamp": str(start_ts),
            "end_timestamp": str(end_ts),
            "duration_days": duration.days,
            "total_bars": total_rows,
            "null_values": null_counts,
            "zero_prices": zero_counts,
            "duplicate_timestamps": duplicates
        }

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
            summary["filtered_bars"] = len(filtered_df)

        print("=========================================================================\n")

        if export_json:
            with open(export_json, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"[+] Exported dataset audit report summary to: {export_json}")

    except Exception as e:
        print(f"Error auditing file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CSV Data Integrity & Timestamp Auditor")
    parser.add_argument("file", type=str, nargs="?", default="XAUUSD_M5.csv", help="Target CSV file name")
    parser.add_argument("--start-date", type=str, default=None, help="Filter dataset from start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default=None, help="Filter dataset up to end date (YYYY-MM-DD)")
    parser.add_argument("--export-summary", type=str, default=None, help="Path to export audit summary JSON")
    parser.add_argument("--all-files", action="store_true", help="Audit all CSV files in csv files/ folder")
    args = parser.parse_args()

    if args.all_files:
        import glob
        files = glob.glob("csv files/*.csv")
        for f in files:
            check_file_integrity(f, start_date=args.start_date, end_date=args.end_date, export_json=args.export_summary)
    else:
        check_file_integrity(args.file, start_date=args.start_date, end_date=args.end_date, export_json=args.export_summary)
