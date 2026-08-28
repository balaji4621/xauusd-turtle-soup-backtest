import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import argparse

def load_data(filepath):
    """Loads XAUUSD data and ensures time index is set properly."""
    try:
        if not os.path.exists(filepath):
            path_in_subdir = os.path.join("csv files", filepath)
            if os.path.exists(path_in_subdir):
                filepath = path_in_subdir
            else:
                print(f"File not found: {filepath}")
                return None
            
        df = pd.read_csv(filepath, sep=None, engine='python')
        if len(df.columns) == 6:
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        date_col = [c for c in df.columns if 'date' in c.lower()][0]
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
    if 2 <= hour < 5: return True
    if (hour == 9 and dt.minute >= 30) or (hour == 10): return True
    return False

def backtest_ict(df, rr_ratio=2.0, swing_period=20, enforce_session=True):
    """Backtests ICT strategy: Liquidity Sweep -> Market Structure Shift -> Fair Value Gap."""
    trades = []
    
    df['swing_high'] = df['high'].rolling(swing_period).max()
    df['swing_low'] = df['low'].rolling(swing_period).min()
    
    for i in range(swing_period, len(df)):
        row = df.iloc[i]
        if enforce_session and not is_in_session(row.name): 
            continue
            
        # Long Setup
        if (row['low'] < df['swing_low'].iloc[i-1]) and (row['close'] > df['swing_high'].iloc[i-1]):
            if df['high'].iloc[i-2] < row['low']:
                entry = row['close']
                sl = df['swing_low'].iloc[i-1]
                risk = entry - sl
                if risk > 0:
                    tp = entry + (risk * rr_ratio)
                    trades.append({'time': row.name, 'type': 'LONG', 'entry': entry, 'sl': sl, 'tp': tp, 'risk': risk})
        
        # Short Setup
        elif (row['high'] > df['swing_high'].iloc[i-1]) and (row['close'] < df['swing_low'].iloc[i-1]):
            if df['low'].iloc[i-2] > row['high']:
                entry = row['close']
                sl = df['swing_high'].iloc[i-1]
                risk = sl - entry
                if risk > 0:
                    tp = entry - (risk * rr_ratio)
                    trades.append({'time': row.name, 'type': 'SHORT', 'entry': entry, 'sl': sl, 'tp': tp, 'risk': risk})
                
    return trades

def print_trade_statistics(trades, filename, rr_ratio):
    """Prints detailed trade breakdown and risk statistics to terminal."""
    longs = sum(1 for t in trades if t['type'] == 'LONG')
    shorts = sum(1 for t in trades if t['type'] == 'SHORT')
    avg_risk = np.mean([t['risk'] for t in trades]) if trades else 0.0
    
    print("\n=========================================================================")
    print(f"               ICT STRATEGY VISUAL ANALYSIS REPORT                      ")
    print("=========================================================================")
    print(f" Target File:         {filename}")
    print(f" Total Trades:        {len(trades)}")
    print(f" Long Positions:      {longs}")
    print(f" Short Positions:     {shorts}")
    print(f" Target R:R Ratio:    {rr_ratio}R")
    print(f" Avg Risk / Trade:    {avg_risk:.2f} pts")
    print("=========================================================================\n")

def plot_results(df, trades, save_path=None, show_plot=True):
    plt.figure(figsize=(14, 7))
    plt.plot(df.index, df['close'], label='Close Price', color='black', alpha=0.4, linewidth=1.0)
    
    long_times = [t['time'] for t in trades if t['type'] == 'LONG']
    long_entries = [t['entry'] for t in trades if t['type'] == 'LONG']
    short_times = [t['time'] for t in trades if t['type'] == 'SHORT']
    short_entries = [t['entry'] for t in trades if t['type'] == 'SHORT']
    
    if long_times:
        plt.scatter(long_times, long_entries, color='green', marker='^', s=60, label='Long Entry', zorder=5)
    if short_times:
        plt.scatter(short_times, short_entries, color='red', marker='v', s=60, label='Short Entry', zorder=5)
    
    plt.title("ICT Liquidity Sweep & Fair Value Gap Entries", fontsize=14)
    plt.xlabel("Date / Time")
    plt.ylabel("Price (XAUUSD)")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300)
        print(f"[+] Saved strategy entry visualization chart to: {save_path}")
        
    if show_plot:
        plt.show()
    plt.close()

def select_preset_interactive():
    """Provides interactive dataset preset selection when run without arguments."""
    presets = {
        "1": ("Daily (D1)", "csv files/XAUUSD_D1.csv"),
        "2": ("4-Hour (H4)", "csv files/XAUUSD_H4.csv"),
        "3": ("1-Hour (H1)", "csv files/XAUUSD_H1.csv"),
        "4": ("15-Minute (M15)", "csv files/XAUUSD_M15.csv"),
        "5": ("5-Minute (M5)", "csv files/XAUUSD_M5.csv")
    }
    return presets.get("1")[1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ICT Strategy Single-File Visualization & Backtest")
    parser.add_argument("file", type=str, nargs="?", default="XAU_15m_data.csv", help="CSV file path to backtest")
    parser.add_argument("--rr", type=float, default=2.0, help="Risk-to-Reward ratio (default: 2.0)")
    parser.add_argument("--swing-period", type=int, default=20, help="Swing high/low lookback period (default: 20)")
    parser.add_argument("--all-hours", action="store_true", help="Disable session filtering (run 24/7)")
    parser.add_argument("--save-plot", type=str, default=None, help="Save chart plot to specified file path")
    parser.add_argument("--no-show", action="store_true", help="Do not render interactive plot window")
    args = parser.parse_args()
    
    target_file = args.file if args.file else select_preset_interactive()
    df = load_data(target_file)
    if df is not None:
        trades = backtest_ict(df, rr_ratio=args.rr, swing_period=args.swing_period, enforce_session=not args.all_hours)
        print_trade_statistics(trades, target_file, args.rr)
        if len(trades) > 0:
            plot_results(df, trades, save_path=args.save_plot, show_plot=not args.no_show)
    else:
        print(f"Could not load {target_file}. Please check the path.")
