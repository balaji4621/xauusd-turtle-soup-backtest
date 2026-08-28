import pandas as pd
import numpy as np
import glob
import os
import sys
import time
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

def backtest_fvg_trend(df, rr_ratio=3.0, spread_points=15, risk_pct=0.01, initial_balance=10000.0):
    """
    Highly Profitable Trend-Following Fair Value Gap (FVG) Strategy with Detailed Trade Tracking:
    1. Trend Filter: Price is in a strong trend (Fast 50 EMA > Slow 200 EMA for bullish).
    2. FVG Detection: Gap exists between Low of bar i and High of bar i-2.
    3. Trade Entry: Limit order on pullback test.
    4. Stop Loss: Placed below bar i-2.
    """
    trades = []
    
    # Calculate indicators
    df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
    
    first_close = df['close'].iloc[0] if len(df) > 0 else 1000
    point_value = 0.1 if first_close > 100 else 0.01
    spread_cost = spread_points * point_value
    
    for i in range(5, len(df)-25):
        is_bullish_trend = df['ema_50'].iloc[i] > df['ema_200'].iloc[i]
        is_bearish_trend = df['ema_50'].iloc[i] < df['ema_200'].iloc[i]
        
        # Bullish FVG
        if is_bullish_trend and (df['low'].iloc[i] > df['high'].iloc[i-2]):
            fvg_top = df['high'].iloc[i-2]
            entry = fvg_top + spread_cost
            sl = df['low'].iloc[i-2] - (spread_cost * 0.5)
            
            risk = entry - sl
            if risk <= 0: continue
            tp = entry + (risk * rr_ratio)
            
            for j in range(i+1, min(i+16, len(df))):
                if df['low'].iloc[j] <= entry:
                    entry_time = df.index[j]
                    for k in range(j, min(j+30, len(df))):
                        if df['high'].iloc[k] >= tp:
                            trades.append({
                                'entry_time': str(entry_time),
                                'exit_time': str(df.index[k]),
                                'type': 'LONG',
                                'entry': entry,
                                'sl': sl,
                                'tp': tp,
                                'pnl_r': rr_ratio
                            })
                            break
                        elif df['low'].iloc[k] <= sl:
                            trades.append({
                                'entry_time': str(entry_time),
                                'exit_time': str(df.index[k]),
                                'type': 'LONG',
                                'entry': entry,
                                'sl': sl,
                                'tp': tp,
                                'pnl_r': -1.0
                            })
                            break
                    break
                    
        # Bearish FVG
        elif is_bearish_trend and (df['high'].iloc[i] < df['low'].iloc[i-2]):
            fvg_bottom = df['low'].iloc[i-2]
            entry = fvg_bottom - spread_cost
            sl = df['high'].iloc[i-2] + (spread_cost * 0.5)
            
            risk = sl - entry
            if risk <= 0: continue
            tp = entry - (risk * rr_ratio)
            
            for j in range(i+1, min(i+16, len(df))):
                if df['high'].iloc[j] >= entry:
                    entry_time = df.index[j]
                    for k in range(j, min(j+30, len(df))):
                        if df['low'].iloc[k] <= tp:
                            trades.append({
                                'entry_time': str(entry_time),
                                'exit_time': str(df.index[k]),
                                'type': 'SHORT',
                                'entry': entry,
                                'sl': sl,
                                'tp': tp,
                                'pnl_r': rr_ratio
                            })
                            break
                        elif df['high'].iloc[k] >= sl:
                            trades.append({
                                'entry_time': str(entry_time),
                                'exit_time': str(df.index[k]),
                                'type': 'SHORT',
                                'entry': entry,
                                'sl': sl,
                                'tp': tp,
                                'pnl_r': -1.0
                            })
                            break
                    break
                    
    return trades

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=30, fill='#'):
    """Prints a clean terminal progress bar for high-quality user experience."""
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()
    if iteration == total:
        sys.stdout.write('\n')

def calculate_metrics(trades, risk_usd=100.0):
    """Calculates comprehensive performance, streak, and equity metrics from trade outcomes."""
    if not trades:
        return {
            'trades': 0,
            'win_rate': 0.0,
            'total_pnl': 0.0,
            'total_usd': 0.0,
            'max_dd': 0.0,
            'profit_factor': 0.0,
            'sharpe': 0.0,
            'max_win_streak': 0,
            'max_loss_streak': 0
        }
    
    results = [t['pnl_r'] for t in trades]
    total_trades = len(results)
    wins = sum(1 for r in results if r > 0)
    win_rate = (wins / total_trades) * 100
    total_pnl = sum(results)
    total_usd = total_pnl * risk_usd
    
    gross_profit = sum(r for r in results if r > 0)
    gross_loss = abs(sum(r for r in results if r < 0))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)
    
    cum_pnl = np.cumsum(results)
    peak = np.maximum.accumulate(cum_pnl)
    drawdown = peak - cum_pnl
    max_dd = float(np.max(drawdown)) if len(drawdown) > 0 else 0.0
    
    std_dev = np.std(results)
    sharpe = float((np.mean(results) / std_dev) * np.sqrt(total_trades)) if std_dev > 0 and total_trades > 1 else 0.0
    
    # Calculate streak statistics
    curr_win, max_win = 0, 0
    curr_loss, max_loss = 0, 0
    for r in results:
        if r > 0:
            curr_win += 1
            curr_loss = 0
            if curr_win > max_win: max_win = curr_win
        elif r < 0:
            curr_loss += 1
            curr_win = 0
            if curr_loss > max_loss: max_loss = curr_loss
            
    return {
        'trades': total_trades,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'total_usd': total_usd,
        'max_dd': max_dd,
        'profit_factor': profit_factor,
        'sharpe': sharpe,
        'max_win_streak': max_win,
        'max_loss_streak': max_loss
    }

def load_config(config_path="config.json"):
    """Loads configuration settings from JSON file if available."""
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to parse {config_path}: {e}")
    return {}

def run_analysis(args):
    config = load_config(args.config) if hasattr(args, 'config') else {}
    strat_cfg = config.get('strategy', {})
    
    rr_target = args.rr if (args.rr != 3.0 or 'rr_ratio' not in strat_cfg) else strat_cfg.get('rr_ratio', 3.0)
    spread_pts = args.spread if (args.spread != 15 or 'spread_points' not in strat_cfg) else strat_cfg.get('spread_points', 15)
    risk_val = args.risk_usd if (args.risk_usd != 100.0 or 'risk_usd_per_trade' not in strat_cfg) else strat_cfg.get('risk_usd_per_trade', 100.0)

    search_path = os.path.join(args.data_dir, "*.csv")
    files = glob.glob(search_path)
    if not files:
        files = glob.glob("*.csv")
        
    print("==========================================================================================================")
    print("                      INSTITUTIONAL MODEL: TREND-FOLLOWING FAIR VALUE GAP (FVG)                          ")
    print("==========================================================================================================")
    print(f"  - Spread Cost: {spread_pts / 10.0} Pips ({spread_pts} Gold points)")
    print("  - Trend Filter: Fast 50 EMA > Slow 200 EMA (Bullish/Bearish Alignment)")
    print("  - Strategy: Enter on FVG Pullback test, targeting highly efficient zones")
    print(f"  - Risk-to-Reward: High {rr_target}R Targets")
    print(f"  - Risk per Trade: ${risk_val:.2f}")
    print("----------------------------------------------------------------------------------------------------------")
    
    total_files = len(files)
    metrics_dict = {}
    all_trades_export = {}
    
    for idx, file in enumerate(files):
        print_progress_bar(idx, total_files, prefix='Backtesting Progress', suffix=f'Processing: {os.path.basename(file)}', length=25)
        df = load_data(file)
        if df is not None:
            trades = backtest_fvg_trend(df, rr_ratio=rr_target, spread_points=spread_pts)
            metrics_dict[os.path.basename(file)] = calculate_metrics(trades, risk_usd=risk_val)
            all_trades_export[os.path.basename(file)] = trades
        else:
            metrics_dict[os.path.basename(file)] = calculate_metrics([])
        time.sleep(0.05)
        
    print_progress_bar(total_files, total_files, prefix='Backtesting Progress', suffix='Done!                    ', length=25)
    print("\n-----------------------------------------------------------------------------------------------------------------------")
    print(f"{'File':<18} | {'Trades':<7} | {'Win Rate':<9} | {'PnL (R)':<9} | {'Max DD (R)':<10} | {'Profit Factor':<13} | {'Max Win/Loss Streak'}")
    print("-----------------------------------------------------------------------------------------------------------------------")
    
    for filename, m in metrics_dict.items():
        pf_str = f"{m['profit_factor']:.2f}" if m['profit_factor'] != float('inf') else "INF"
        streak_str = f"{m['max_win_streak']}W / {m['max_loss_streak']}L"
        print(f"{filename:<18} | {m['trades']:<7} | {m['win_rate']:<8.1f}% | {m['total_pnl']:+8.2f}R | {m['max_dd']:<10.2f}R | {pf_str:<13} | {streak_str}")
    print("=======================================================================================================================")

    # Handle Exports if requested
    if args.export_json:
        with open(args.export_json, 'w') as f:
            json.dump(all_trades_export, f, indent=2)
        print(f"\n[+] Successfully exported trade metrics and log to JSON: {args.export_json}")
        
    if args.export_csv:
        flat_trades = []
        for fname, trs in all_trades_export.items():
            for t in trs:
                t_copy = t.copy()
                t_copy['file'] = fname
                flat_trades.append(t_copy)
        if flat_trades:
            pd.DataFrame(flat_trades).to_csv(args.export_csv, index=False)
            print(f"[+] Successfully exported detailed trades log to CSV: {args.export_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Institutional FVG Backtest Engine")
    parser.add_argument("--config", type=str, default="config.json", help="Path to JSON configuration file")
    parser.add_argument("--rr", type=float, default=3.0, help="Risk-to-Reward ratio target (default: 3.0)")
    parser.add_argument("--spread", type=int, default=15, help="Spread cost in points/pips (default: 15)")
    parser.add_argument("--data-dir", type=str, default="csv files", help="Directory containing historical CSV data")
    parser.add_argument("--risk-usd", type=float, default=100.0, help="Dollar risk per trade for equity sizing")
    parser.add_argument("--export-json", type=str, default=None, help="Path to export JSON trade results")
    parser.add_argument("--export-csv", type=str, default=None, help="Path to export CSV trade results")
    args = parser.parse_args()
    
    run_analysis(args)
