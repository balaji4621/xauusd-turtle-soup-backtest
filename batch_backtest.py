import pandas as pd
import glob

def load_data(filepath):
    """Loads CSV files, automatically detecting if there is a header or not."""
    try:
        # Using sep=None and engine='python' to auto-detect the separator (comma or semicolon)
        df = pd.read_csv(filepath, sep=None, engine='python')
        
        # If the first row is a header, columns will be names. 
        # If not, they will be 0, 1, 2...
        # Let's force standard names if the detection seems wrong.
        if len(df.columns) == 6:
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        
        df['date'] = pd.to_datetime(df['date'], format='mixed')
        df.set_index('date', inplace=True)
        return df[['open', 'high', 'low', 'close']].sort_index()
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def backtest_ict(df):
    """Loose logic to identify if the strategy/data is working."""
    trades = []
    # Using a 20-period lookback for liquidity
    df['swing_high'] = df['high'].rolling(20).max().shift(1)
    df['swing_low'] = df['low'].rolling(20).min().shift(1)
    
    for i in range(20, len(df)):
        row = df.iloc[i]
        # Bullish: Price closed above the 20-period high
        if row['close'] > df['swing_high'].iloc[i]:
            trades.append({'type': 'LONG'})
        # Bearish: Price closed below the 20-period low
        elif row['close'] < df['swing_low'].iloc[i]:
            trades.append({'type': 'SHORT'})
    return trades

def run_batch():
    files = glob.glob("*.csv") + glob.glob("csv files/*.csv")
    print(f"Processing {len(files)} files...")
    for file in files:
        df = load_data(file)
        if df is not None:
            trades = backtest_ict(df)
            print(f"{file}: {len(trades)} trades identified")
        else:
            print(f"Failed to process: {file}")

if __name__ == "__main__":
    run_batch()
