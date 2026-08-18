import pandas as pd
import glob
import os

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

def is_in_active_session(dt):
    """
    Filters for liquid sessions:
    - London: 2:00 - 8:00 EST
    - New York: 8:00 - 12:00 EST
    """
    hour = dt.hour
    return (2 <= hour < 12)

def backtest_smart_money(df, rr_ratio=2.0, spread_points=15, use_session_filter=True):
    """
    Turtle Soup Reversal Logic with Realistic Costs:
    1. Liquidity Sweep (Price breaches swing, then closes back inside).
    2. Trade the reversal.
    3. spread_points is in Gold ticks/points (10 points = 1.0 USD/Pip on Gold).
       - e.g., 15 points = $1.50 spread.
    """
    results = []
    # 20-period swing points as structure
    df['swing_high'] = df['high'].rolling(20).max().shift(1)
    df['swing_low'] = df['low'].rolling(20).min().shift(1)
    
    # Convert spread to absolute price units
    # For Gold (XAUUSD), if prices are around 400-2000, 1 point is 0.1 or 0.01 depending on digits.
    # We will automatically detect point value. If close price > 100, 1 point is typically 0.1 (e.g. 1800.5 to 1800.6)
    first_close = df['close'].iloc[0] if len(df) > 0 else 1000
    point_value = 0.1 if first_close > 100 else 0.01
    spread_cost = spread_points * point_value
    
    for i in range(21, len(df)-5):
        current_time = df.index[i]
        
        # Apply Session Filter
        if use_session_filter and not is_in_active_session(current_time):
            continue
            
        # 1. Sweep Low, then close ABOVE swing low (Bullish Reversal / LONG Setup)
        if df['low'].iloc[i] < df['swing_low'].iloc[i] and df['close'].iloc[i] > df['swing_low'].iloc[i]:
            entry = df['close'].iloc[i] + spread_cost  # Pay spread on buy entry
            sl = df['low'].iloc[i] 
            
            # Risk after including spread
            risk = entry - sl
            if risk <= 0:
                continue
                
            tp = entry + (risk * rr_ratio)
            
            # Check outcome in next 15 bars
            for j in range(i+1, min(i+16, len(df))):
                if df['high'].iloc[j] >= tp:
                    results.append(rr_ratio)
                    break
                elif df['low'].iloc[j] <= sl:
                    results.append(-1.0)
                    break
        
        # 2. Sweep High, then close BELOW swing high (Bearish Reversal / SHORT Setup)
        elif df['high'].iloc[i] > df['swing_high'].iloc[i] and df['close'].iloc[i] < df['swing_high'].iloc[i]:
            entry = df['close'].iloc[i] - spread_cost  # Lose spread on sell entry
            sl = df['high'].iloc[i]
            
            # Risk after including spread
            risk = sl - entry
            if risk <= 0:
                continue
                
            tp = entry - (risk * rr_ratio)
            
            # Check outcome in next 15 bars
            for j in range(i+1, min(i+16, len(df))):
                if df['low'].iloc[j] <= tp:
                    results.append(rr_ratio)
                    break
                elif df['high'].iloc[j] >= sl:
                    results.append(-1.0)
                    break
    return results

def run_analysis():
    files = glob.glob("csv files/*.csv")
    print(f"Running backtest with: ")
    print(f"  - Spread: 1.5 Pips (15 Gold points)")
    print(f"  - Session Filter: London & New York Active Hours (02:00 - 12:00 EST)")
    print("-" * 75)
    print(f"{'File':<25} | {'Trades':<8} | {'Win Rate':<10} | {'Total PnL (R)'}")
    print("-" * 75)
    
    for file in files:
        df = load_data(file)
        if df is not None:
            results = backtest_smart_money(df, rr_ratio=2.0, spread_points=15, use_session_filter=True)
            if results:
                win_rate = (sum(1 for r in results if r > 0) / len(results)) * 100
                total_pnl = sum(results)
                print(f"{os.path.basename(file):<25} | {len(results):<8} | {win_rate:<9.1f}% | {total_pnl:.2f}R")
            else:
                print(f"{os.path.basename(file):<25} | 0        | 0.0%       | 0.00R")

if __name__ == "__main__":
    run_analysis()
