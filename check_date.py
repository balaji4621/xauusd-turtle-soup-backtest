import pandas as pd
df = pd.read_csv('csv files/XAUUSD_M5.csv', names=['date', 'open', 'high', 'low', 'close', 'volume'])
df['date'] = pd.to_datetime(df['date'])
print(f'Start: {df["date"].min()}')
print(f'End: {df["date"].max()}')
print(f'Total Duration: {df["date"].max() - df["date"].min()}')
