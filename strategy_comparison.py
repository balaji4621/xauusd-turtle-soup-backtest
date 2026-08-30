import pandas as pd
import numpy as np
import os
import argparse
import json
from pnl_backtest import backtest_fvg_trend, load_data
from orderblock_backtest import backtest_ob_liquidity_fast

def run_benchmark(rr_ratio=3.0, spread_points=15, export_json=None, export_csv=None):
    print("=" * 85)
    print("           QUANTITATIVE STRATEGY BENCHMARK COMPARISON ENGINE (XAUUSD)")
    print("=" * 85)
    print(f" Target R:R: {rr_ratio}R  |  Spread: {spread_points/10.0} Pips ({spread_points} Points)")
    print("-" * 85)

    files = {
        "D1 (Daily)": "csv files/XAUUSD_D1.csv",
        "H4 (4-Hour)": "csv files/XAUUSD_H4.csv",
        "H1 (1-Hour)": "csv files/XAUUSD_H1.csv",
        "M30 (30-Min)": "csv files/XAUUSD_M30.csv",
        "M15 (15-Min)": "csv files/XAUUSD_M15.csv",
        "M5 (5-Min)": "csv files/XAUUSD_M5.csv"
    }

    base_dir = os.path.dirname(os.path.abspath(__file__))
    comparison_rows = []

    for name, rel_path in files.items():
        full_path = os.path.join(base_dir, rel_path)
        if not os.path.exists(full_path):
            continue

        df = load_data(full_path)
        if df is None or len(df) == 0:
            continue

        # Strategy 1: FVG Trend-Following
        fvg_trades = backtest_fvg_trend(df, rr_ratio=rr_ratio, spread_points=spread_points)
        fvg_results = [t['pnl_r'] for t in fvg_trades]
        fvg_r = sum(fvg_results)
        fvg_wr = (sum(1 for r in fvg_results if r > 0) / len(fvg_results) * 100) if fvg_results else 0.0

        # Strategy 2: Order Block Liquidity Sweep
        ob_trades = backtest_ob_liquidity_fast(df, rr_ratio=rr_ratio, spread_points=spread_points)
        ob_results = [t['pnl_r'] for t in ob_trades]
        ob_r = sum(ob_results)
        ob_wr = (sum(1 for r in ob_results if r > 0) / len(ob_results) * 100) if ob_results else 0.0

        best_strategy = "FVG Trend" if fvg_r > ob_r else "Order Block"

        comparison_rows.append({
            "Timeframe": name,
            "FVG Trades": len(fvg_results),
            "FVG WinRate": f"{fvg_wr:.1f}%",
            "FVG Return": f"{fvg_r:+.2f}R",
            "OB Trades": len(ob_results),
            "OB WinRate": f"{ob_wr:.1f}%",
            "OB Return": f"{ob_r:+.2f}R",
            "Top Model": best_strategy
        })

    summary_df = pd.DataFrame(comparison_rows)
    print("\n" + summary_df.to_string(index=False) + "\n")
    print("=" * 85)

    if export_json:
        with open(export_json, 'w') as f:
            json.dump(comparison_rows, f, indent=2)
        print(f"[+] Exported benchmark comparison matrix to JSON: {export_json}")

    if export_csv:
        summary_df.to_csv(export_csv, index=False)
        print(f"[+] Exported benchmark comparison matrix to CSV: {export_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Strategy Benchmark Engine")
    parser.add_argument("--rr", type=float, default=3.0, help="Target R:R ratio (default: 3.0)")
    parser.add_argument("--spread", type=int, default=15, help="Spread cost in points (default: 15)")
    parser.add_argument("--export-json", type=str, default=None, help="Path to export benchmark JSON")
    parser.add_argument("--export-csv", type=str, default=None, help="Path to export benchmark CSV")
    args = parser.parse_args()

    run_benchmark(rr_ratio=args.rr, spread_points=args.spread, export_json=args.export_json, export_csv=args.export_csv)