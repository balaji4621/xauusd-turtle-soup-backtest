import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

def load_data(filepath):
    """Loads XAUUSD data and ensures time index is set."""
    try:
        # Check if file exists in the direct project folder or the 'csv files' folder
        if not os.path.exists(filepath):
            # Attempt to find it in the 'csv files' folder
            path_in_subdir = os.path.join("csv files", filepath)
            if os.path.exists(path_in_subdir):
                filepath = path_in_subdir
            else:
                print(f"File not found: {filepath}")
                return None
            
        df = pd.read_csv(filepath, sep=';')
        # Find date column
        date_col = [c for c in df.columns if 'date' in c.lower()][0]
        # Handle different potential date formats
        df[date_col] = pd.to_datetime(df[date_col], format='mixed')
        df.set_index(date_col, inplace=True)
        df.columns = [c.lower() for c in df.columns]
        return df[['open', 'high', 'low', 'close']].sort_index()
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def is_in_session(dt):
    """Checks if the time is within NY AM (9:30-11:00 EST) or London (2:00-5:00 EST)."""
    hour = dt.hour
    # London (2-5 EST)
    if 2 <= hour < 5: return True
    # NY AM (9:30-11:00 EST)
    if (hour == 9 and dt.minute >= 30) or (hour == 10): return True
    return False

def backtest_ict(df, rr_ratio=2.0):
    """Backtests ICT strategy: Liquidity Sweep -> MSS -> FVG."""
    trades = []
    
    # Pre-calculate rolling high/low
    df['swing_high'] = df['high'].rolling(20).max()
    df['swing_low'] = df['low'].rolling(20).min()
    
    for i in range(20, len(df)):
        row = df.iloc[i]
        if not is_in_session(row.name): continue
            
        # Long Setup
        if (row['low'] < df['swing_low'].iloc[i-1]) and (row['close'] > df['swing_high'].iloc[i-1]):
            if df['high'].iloc[i-2] < row['low']:
                entry = row['close']
                sl = df['swing_low'].iloc[i-1]
                tp = entry + (entry - sl) * rr_ratio
                trades.append({'time': row.name, 'type': 'LONG', 'entry': entry, 'sl': sl, 'tp': tp})
        
        # Short Setup
        elif (row['high'] > df['swing_high'].iloc[i-1]) and (row['close'] < df['swing_low'].iloc[i-1]):
            if df['low'].iloc[i-2] > row['high']:
                entry = row['close']
                sl = df['swing_high'].iloc[i-1]
                tp = entry - (sl - entry) * rr_ratio
                trades.append({'time': row.name, 'type': 'SHORT', 'entry': entry, 'sl': sl, 'tp': tp})
                
    return trades

def plot_results(df, trades):
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df['close'], label='Close Price', color='black', alpha=0.5)
    
    for t in trades:
        color = 'green' if t['type'] == 'LONG' else 'red'
        plt.scatter(t['time'], t['entry'], color=color, marker='^' if t['type'] == 'LONG' else 'v')
    
    plt.title("ICT Strategy Entries")
    plt.legend()
    plt.show()

if __name__ == "__main__":
    # Usage: python backtest_ict.py "XAUUSD_M15.csv"
    filename = sys.argv[1] if len(sys.argv) > 1 else "XAU_15m_data.csv"
    df = load_data(filename)
    if df is not None:
        trades = backtest_ict(df)
        print(f"Backtest for {filename} complete. {len(trades)} trades identified.")
        if len(trades) > 0:
            plot_results(df, trades)
    else:
        print(f"Could not load {filename}. Please check the path.")
