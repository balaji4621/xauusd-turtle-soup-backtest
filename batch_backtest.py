import pandas as pd
import glob
import os
import argparse
import logging
import json
from concurrent.futures import ProcessPoolExecutor, as_completed

def load_config(config_path="config.json"):
    """Loads configuration settings from JSON file if available."""
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Failed to read {config_path}: {e}")
    return {}

# Setup logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

def load_data(filepath):
    """Loads CSV files, automatically detecting format and columns."""
    try:
        df = pd.read_csv(filepath, sep=None, engine='python')
        if len(df.columns) == 6:
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        
        date_col = [c for c in df.columns if 'date' in c.lower()][0]
        df[date_col] = pd.to_datetime(df[date_col], format='mixed')
        df.set_index(date_col, inplace=True)
        return df[['open', 'high', 'low', 'close']].sort_index()
    except Exception as e:
        logging.error(f"Failed to load {filepath}: {e}")
        return None

def backtest_ict(df, swing_period=20):
    """Identifies liquidity sweep setup entries with configurable swing lookback."""
    trades = []
    df['swing_high'] = df['high'].rolling(swing_period).max().shift(1)
    df['swing_low'] = df['low'].rolling(swing_period).min().shift(1)
    
    for i in range(swing_period, len(df)):
        row = df.iloc[i]
        if row['close'] > df['swing_high'].iloc[i]:
            trades.append({'type': 'LONG', 'price': row['close'], 'time': str(row.name)})
        elif row['close'] < df['swing_low'].iloc[i]:
            trades.append({'type': 'SHORT', 'price': row['close'], 'time': str(row.name)})
    return trades

def process_file_task(args_tuple):
    filepath, swing_period = args_tuple
    df = load_data(filepath)
    if df is not None:
        trades = backtest_ict(df, swing_period=swing_period)
        return filepath, len(trades), True
    return filepath, 0, False

def run_batch(swing_period=20, parallel=True, workers=4):
    files = list(set(glob.glob("*.csv") + glob.glob("csv files/*.csv")))
    logging.info(f"Initiating batch processing across {len(files)} dataset files...")
    logging.info(f"Configuration: Swing Period={swing_period}, Parallel={parallel}, Max Workers={workers}")
    
    results = {}
    if parallel and len(files) > 1:
        tasks = [(f, swing_period) for f in files]
        with ProcessPoolExecutor(max_workers=min(workers, len(files))) as executor:
            future_map = {executor.submit(process_file_task, task): task[0] for task in tasks}
            for future in as_completed(future_map):
                filepath, trade_count, success = future.result()
                if success:
                    results[filepath] = trade_count
                    logging.info(f"Completed {os.path.basename(filepath)}: {trade_count} trades identified")
                else:
                    logging.warning(f"Failed processing {filepath}")
    else:
        for file in files:
            filepath, trade_count, success = process_file_task((file, swing_period))
            if success:
                results[filepath] = trade_count
                logging.info(f"Completed {os.path.basename(filepath)}: {trade_count} trades identified")
            else:
                logging.warning(f"Failed processing {filepath}")

    print("\n" + "="*60)
    print(f"{'Filename':<35} | {'Trades Identified':<20}")
    print("="*60)
    for fname, count in results.items():
        print(f"{os.path.basename(fname):<35} | {count:<20}")
    print("="*60 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch High-Performance ICT Strategy Runner")
    parser.add_argument("--config", type=str, default="config.json", help="Path to JSON configuration file")
    parser.add_argument("--swing-period", type=int, default=20, help="Swing lookback period (default: 20)")
    parser.add_argument("--no-parallel", action="store_true", help="Disable multiprocessing parallel execution")
    parser.add_argument("--workers", type=int, default=4, help="Maximum parallel worker processes (default: 4)")
    args = parser.parse_args()

    cfg = load_config(args.config)
    swing_val = args.swing_period if (args.swing_period != 20 or 'strategy' not in cfg) else cfg.get('strategy', {}).get('swing_lookback', 20)

    run_batch(swing_period=swing_val, parallel=not args.no_parallel, workers=args.workers)
