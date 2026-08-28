import pandas as pd
import numpy as np
import os
import sys
import argparse
import json

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

def backtest_ob_liquidity_fast(df, rr_ratio=3.0, spread_points=15, swing_lookback=20):
    df = df.copy()
    
    close = df['close'].to_numpy()
    high = df['high'].to_numpy()
    low = df['low'].to_numpy()
    
    ema_50 = df['close'].ewm(span=50, adjust=False).mean().to_numpy()
    ema_200 = df['close'].ewm(span=200, adjust=False).mean().to_numpy()
    
    high_low = high - low
    high_close = np.abs(high - np.roll(close, 1))
    low_close = np.abs(low - np.roll(close, 1))
    tr = np.maximum(high_low, np.maximum(high_close, low_close))
    atr = pd.Series(tr).rolling(14).mean().to_numpy()
    
    point_value = 0.1 if (len(close) > 0 and close[0] > 100) else 0.01
    spread_cost = spread_points * point_value
    
    win_high = df['high'].shift(1).rolling(swing_lookback).max().to_numpy()
    win_low = df['low'].shift(1).rolling(swing_lookback).min().to_numpy()
    
    n = len(df)
    results = []
    
    bull_signals = np.where((low < win_low) & (close > win_low) & (ema_50 > ema_200))[0]
    bear_signals = np.where((high > win_high) & (close < win_high) & (ema_50 < ema_200))[0]
    
    for i in bull_signals:
        if i < swing_lookback + 5 or i >= n - 20:
            continue
        entry = close[i] + spread_cost
        sl = low[i] - (spread_cost * 0.5) - (atr[i] * 0.1 if not np.isnan(atr[i]) else 0.2)
        risk = entry - sl
        if risk <= 0:
            continue
        tp = entry + (risk * rr_ratio)
        
        end_idx = min(i + 21, n)
        highs_fwd = high[i+1:end_idx]
        lows_fwd = low[i+1:end_idx]
        
        hit_tp = np.where(highs_fwd >= tp)[0]
        hit_sl = np.where(lows_fwd <= sl)[0]
        
        first_tp = hit_tp[0] if len(hit_tp) > 0 else 999
        first_sl = hit_sl[0] if len(hit_sl) > 0 else 999
        
        if first_tp < first_sl:
            results.append({'type': 'LONG', 'pnl_r': rr_ratio, 'entry': entry, 'sl': sl, 'tp': tp})
        elif first_sl < first_tp:
            results.append({'type': 'LONG', 'pnl_r': -1.0, 'entry': entry, 'sl': sl, 'tp': tp})
            
    for i in bear_signals:
        if i < swing_lookback + 5 or i >= n - 20:
            continue
        entry = close[i] - spread_cost
        sl = high[i] + (spread_cost * 0.5) + (atr[i] * 0.1 if not np.isnan(atr[i]) else 0.2)
        risk = sl - entry
        if risk <= 0:
            continue
        tp = entry - (risk * rr_ratio)
        
        end_idx = min(i + 21, n)
        highs_fwd = high[i+1:end_idx]
        lows_fwd = low[i+1:end_idx]
        
        hit_tp = np.where(lows_fwd <= tp)[0]
        hit_sl = np.where(highs_fwd >= sl)[0]
        
        first_tp = hit_tp[0] if len(hit_tp) > 0 else 999
        first_sl = hit_sl[0] if len(hit_sl) > 0 else 999
        
        if first_tp < first_sl:
            results.append({'type': 'SHORT', 'pnl_r': rr_ratio, 'entry': entry, 'sl': sl, 'tp': tp})
        elif first_sl < first_tp:
            results.append({'type': 'SHORT', 'pnl_r': -1.0, 'entry': entry, 'sl': sl, 'tp': tp})
            
    return results

def run_suite(args=None):
    rr_target = args.rr if args else 3.0
    spread_pts = args.spread if args else 15
    swing_period = args.swing_lookback if args else 20

    print("=" * 70)
    print("  INSTITUTIONAL ORDER BLOCK & LIQUIDITY SWEEP BACKTEST (XAUUSD)")
    print("=" * 70)
    print(f" Target R:R: {rr_target}R | Spread: {spread_pts/10.0} pips | Swing: {swing_period} bars")
    print("-" * 70)
    
    files = {
        "D1 (Daily)": "csv files/XAUUSD_D1.csv",
        "H4 (4-Hour)": "csv files/XAUUSD_H4.csv",
        "H1 (1-Hour)": "csv files/XAUUSD_H1.csv",
        "M30 (30-Min)": "csv files/XAUUSD_M30.csv",
        "M15 (15-Min)": "csv files/XAUUSD_M15.csv",
        "M5 (5-Min)": "csv files/XAUUSD_M5.csv"
    }
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    summary_data = []
    export_dict = {}

    for name, rel_path in files.items():
        full_path = os.path.join(base_dir, rel_path)
        if not os.path.exists(full_path):
            continue
            
        df = load_data(full_path)
        if df is None or len(df) == 0:
            continue
            
        trades = backtest_ob_liquidity_fast(df, rr_ratio=rr_target, spread_points=spread_pts, swing_lookback=swing_period)
        export_dict[name] = trades
        total_trades = len(trades)
        
        if total_trades > 0:
            results = [t['pnl_r'] for t in trades]
            wins = sum(1 for r in results if r > 0)
            losses = sum(1 for r in results if r < 0)
            win_rate = (wins / total_trades) * 100
            total_r = sum(results)
            gross_win = wins * rr_target
            gross_loss = losses * 1.0
            profit_factor = (gross_win / gross_loss) if gross_loss > 0 else 99.0
            
            # Risk & Equity metrics
            cum_pnl = np.cumsum(results)
            peak = np.maximum.accumulate(cum_pnl)
            max_dd = float(np.max(peak - cum_pnl)) if len(cum_pnl) > 0 else 0.0
            std_dev = np.std(results)
            sharpe = float((np.mean(results) / std_dev) * np.sqrt(total_trades)) if std_dev > 0 and total_trades > 1 else 0.0
            
            status = "[PROFITABLE]" if total_r > 0 else "[LOSS]"
        else:
            wins, losses, win_rate, total_r, profit_factor, max_dd, sharpe = 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0
            status = "[NO TRADES]"

        summary_data.append({
            "Timeframe": name,
            "Trades": total_trades,
            "Win Rate": f"{win_rate:.1f}%",
            "Profit Factor": f"{profit_factor:.2f}",
            "Net Return (R)": f"{total_r:+.2f}R",
            "Max DD (R)": f"{max_dd:.2f}R",
            "Sharpe": f"{sharpe:.2f}",
            "Status": status
        })

    summary_df = pd.DataFrame(summary_data)
    print("\n" + summary_df.to_string(index=False) + "\n")
    print("=" * 70)

    if args and args.export_json:
        with open(args.export_json, 'w') as f:
            json.dump(export_dict, f, indent=2)
        print(f"[+] Exported order block backtest results to: {args.export_json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Order Block & Liquidity Sweep Backtest")
    parser.add_argument("--rr", type=float, default=3.0, help="Target Risk-to-Reward ratio (default: 3.0)")
    parser.add_argument("--spread", type=int, default=15, help="Spread cost in points/pips (default: 15)")
    parser.add_argument("--swing-lookback", type=int, default=20, help="Swing lookback period (default: 20)")
    parser.add_argument("--export-json", type=str, default=None, help="Path to export JSON trade log")
    args = parser.parse_args()
    
    run_suite(args)
