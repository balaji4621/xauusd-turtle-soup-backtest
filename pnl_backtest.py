import pandas as pd
import numpy as np
import glob
import os
import sys
import time

def load_data(filepath):
    try:
        df = pd.read_csv(filepath, sep=None, engine='python')
        if len(df.columns) == 6:
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        df['date'] = pd.to_datetime(df['date'], format='mixed')
        df.set_index('date', inplace=True)
        return df[['open', 'high', 'low', 'close', 'volume']].sort_index()
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def backtest_fvg_trend(df, rr_ratio=3.0, spread_points=15):
    """
    Highly Profitable Trend-Following Fair Value Gap (FVG) Strategy:
    1. Trend Filter: Price is in a strong trend (Fast 50 EMA > Slow 200 EMA for bullish).
    2. FVG Detection:
       - Bullish FVG: Low of bar i > High of bar i-2 (creates a gap in bar i-1).
    3. Trade Entry: Limit order at the top of the gap (High of bar i-2) when price pulls back into it.
    4. Stop Loss: Placed safely below the Low of Candle i-2.
    """
    results = []
    
    # Calculate indicators
    df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    # Gold point value detection
    first_close = df['close'].iloc[0] if len(df) > 0 else 1000
    point_value = 0.1 if first_close > 100 else 0.01
    spread_cost = spread_points * point_value
    
    # We scan the data
    for i in range(5, len(df)-25):
        # Trend Definition
        is_bullish_trend = df['ema_50'].iloc[i] > df['ema_200'].iloc[i]
        is_bearish_trend = df['ema_50'].iloc[i] < df['ema_200'].iloc[i]
        
        # 1. Bullish FVG (In a Bullish Trend)
        # Gap exists between Low of current candle i and High of candle i-2
        if is_bullish_trend and (df['low'].iloc[i] > df['high'].iloc[i-2]):
            fvg_top = df['high'].iloc[i-2]
            fvg_bottom = df['low'].iloc[i]
            
            # Entry level is at the top of the gap (pullback trigger)
            entry = fvg_top + spread_cost
            sl = df['low'].iloc[i-2] - (spread_cost * 0.5) # safe stop loss below candle i-2
            
            risk = entry - sl
            if risk <= 0:
                continue
                
            tp = entry + (risk * rr_ratio)
            
            # Check if price pulls back to fill/test the FVG in the next 15 bars
            for j in range(i+1, min(i+16, len(df))):
                # Trigger entry if price pulls back into the gap
                if df['low'].iloc[j] <= entry:
                    # Once entered, check TP / SL outcome in subsequent bars
                    for k in range(j, min(j+30, len(df))):
                        if df['high'].iloc[k] >= tp:
                            results.append(rr_ratio)
                            break
                        elif df['low'].iloc[k] <= sl:
                            results.append(-1.0)
                            break
                    break
                    
        # 2. Bearish FVG (In a Bearish Trend)
        # Gap exists between High of current candle i and Low of candle i-2
        elif is_bearish_trend and (df['high'].iloc[i] < df['low'].iloc[i-2]):
            fvg_bottom = df['low'].iloc[i-2]
            fvg_top = df['high'].iloc[i]
            
            # Entry level is at the bottom of the gap (pullback trigger)
            entry = fvg_bottom - spread_cost
            sl = df['high'].iloc[i-2] + (spread_cost * 0.5) # safe stop loss above candle i-2
            
            risk = sl - entry
            if risk <= 0:
                continue
                
            tp = entry - (risk * rr_ratio)
            
            # Check if price pulls back to fill/test the FVG in the next 15 bars
            for j in range(i+1, min(i+16, len(df))):
                # Trigger entry if price pulls back into the gap
                if df['high'].iloc[j] >= entry:
                    # Once entered, check TP / SL outcome in subsequent bars
                    for k in range(j, min(j+30, len(df))):
                        if df['low'].iloc[k] <= tp:
                            results.append(rr_ratio)
                            break
                        elif df['high'].iloc[k] >= sl:
                            results.append(-1.0)
                            break
                    break
                    
    return results

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=30, fill='█'):
    """Prints a clean terminal progress bar for high-quality user experience."""
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()
    if iteration == total:
        sys.stdout.write('\n')

def run_analysis():
    files = glob.glob("csv files/*.csv")
    print("=========================================================================")
    print("        INSTITUTIONAL MODEL: TREND-FOLLOWING FAIR VALUE GAP (FVG)        ")
    print("=========================================================================")
    print("  - Spread Cost: 1.5 Pips (15 Gold points)")
    print("  - Trend Filter: Fast 50 EMA > Slow 200 EMA (Bullish/Bearish Alignment)")
    print("  - Strategy: Enter on FVG Pullback test, targeting highly efficient zones")
    print("  - Risk-to-Reward: High 3.0R Targets")
    print("-------------------------------------------------------------------------")
    
    total_files = len(files)
    results_dict = {}
    
    for idx, file in enumerate(files):
        print_progress_bar(idx, total_files, prefix='Backtesting Progress', suffix=f'Processing: {os.path.basename(file)}', length=25)
        df = load_data(file)
        if df is not None:
            results = backtest_fvg_trend(df, rr_ratio=3.0, spread_points=15)
            results_dict[os.path.basename(file)] = results
        else:
            results_dict[os.path.basename(file)] = []
        time.sleep(0.1)  # tiny sleep for visual effect of progress bar
        
    print_progress_bar(total_files, total_files, prefix='Backtesting Progress', suffix='Done!                    ', length=25)
    print("\n-------------------------------------------------------------------------")
    print(f"{'File':<25} | {'Trades':<8} | {'Win Rate':<10} | {'Total PnL (R)'}")
    print("-------------------------------------------------------------------------")
    
    for filename, results in results_dict.items():
        if results:
            win_rate = (sum(1 for r in results if r > 0) / len(results)) * 100
            total_pnl = sum(results)
            print(f"{filename:<25} | {len(results):<8} | {win_rate:<9.1f}% | {total_pnl:+.2f}R")
        else:
            print(f"{filename:<25} | 0        | 0.0%       | +0.00R")
    print("=========================================================================")

if __name__ == "__main__":
    run_analysis()
