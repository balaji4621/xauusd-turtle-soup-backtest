import unittest
import pandas as pd
import numpy as np
import os
import sys

# Ensure parent directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pnl_backtest import calculate_metrics, load_data, backtest_fvg_trend
from orderblock_backtest import backtest_ob_liquidity_fast
from strategy_comparison import run_benchmark
from check_date import check_file_integrity

class TestQuantStrategy(unittest.TestCase):

    def test_calculate_metrics_empty(self):
        metrics = calculate_metrics([])
        self.assertEqual(metrics['trades'], 0)
        self.assertEqual(metrics['win_rate'], 0.0)
        self.assertEqual(metrics['total_pnl'], 0.0)
        self.assertEqual(metrics['max_dd'], 0.0)
        self.assertEqual(metrics['profit_factor'], 0.0)

    def test_calculate_metrics_positive(self):
        trades = [
            {'pnl_r': 3.0},
            {'pnl_r': -1.0},
            {'pnl_r': 3.0},
            {'pnl_r': -1.0}
        ]
        metrics = calculate_metrics(trades, risk_usd=100.0)
        self.assertEqual(metrics['trades'], 4)
        self.assertEqual(metrics['win_rate'], 50.0)
        self.assertEqual(metrics['total_pnl'], 4.0)
        self.assertEqual(metrics['total_usd'], 400.0)
        self.assertEqual(metrics['profit_factor'], 3.0)
        self.assertEqual(metrics['max_win_streak'], 1)
        self.assertEqual(metrics['max_loss_streak'], 1)

    def test_load_data_valid(self):
        file_path = os.path.join("csv files", "XAUUSD_D1.csv")
        if os.path.exists(file_path):
            df = load_data(file_path)
            self.assertIsNotNone(df)
            self.assertFalse(df.empty)
            self.assertIn('close', df.columns)
            self.assertIn('high', df.columns)
            self.assertIn('low', df.columns)

    def test_backtest_fvg_trend_execution(self):
        file_path = os.path.join("csv files", "XAUUSD_D1.csv")
        if os.path.exists(file_path):
            df = load_data(file_path)
            trades = backtest_fvg_trend(df, rr_ratio=3.0, spread_points=15)
            self.assertIsInstance(trades, list)

    def test_backtest_ob_liquidity_execution(self):
        file_path = os.path.join("csv files", "XAUUSD_D1.csv")
        if os.path.exists(file_path):
            df = load_data(file_path)
            trades = backtest_ob_liquidity_fast(df, rr_ratio=3.0, spread_points=15)
            self.assertIsInstance(trades, list)

    def test_strategy_comparison_benchmark(self):
        file_path = os.path.join("csv files", "XAUUSD_D1.csv")
        if os.path.exists(file_path):
            results = run_benchmark(rr_ratio=3.0, spread_points=15)
            self.assertIsNone(results)

    def test_check_date_audit(self):
        file_path = os.path.join("csv files", "XAUUSD_D1.csv")
        if os.path.exists(file_path):
            check_file_integrity(file_path)

if __name__ == '__main__':
    unittest.main()