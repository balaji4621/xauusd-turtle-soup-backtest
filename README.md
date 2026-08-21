# XAUUSD Institutional Trend-Following & Fair Value Gap (FVG) Backtesting Suite

A professional quantitative trading engine built to analyze and optimize price-action trading strategies on Gold (XAUUSD) across multiple timeframes. 

This repository documents the complete evolution of an algorithmic trading model: from a raw **Turtle Soup Reversal** concept to an optimized, **highly profitable Institutional Trend-Following Fair Value Gap (FVG)** model that holds up under realistic 1.5-pip spread transaction costs on higher timeframes.

---

## 📁 Repository Structure
* `pnl_backtest.py` - The main quantitative backtesting engine featuring our profitable FVG Trend system.
* `orderblock_backtest.py` - Institutional Order Block & Liquidity Sweep backtest engine.
* `backtest_ict.py` - Single-file visualization script showing Precise entry and exit setups on charts.
* `batch_backtest.py` - Batch processing script to quickly parse multiple market CSV files.
* `ICT_Turtle_Soup.pine` - Production-ready TradingView Pine Script (v5) containing strategy and dynamic breakeven stop management.
* `csv files/` - Folder containing historical XAUUSD data from `M1` up to `D1` timeframes.

---

## 🔬 Strategy Evolution & Quantitative Discoveries

### Phase 1: The "Turtle Soup Reversal" (Theoretical vs. Realistic)
Initially, we tested a pure counter-trend Turtle Soup Reversal (entering immediately on liquidity sweeps). 
* **The Illusion:** In a 24/7 backtest with no fees, it showed a massive **+1,371R** on 15-minute data.
* **The Reality:** When we added a realistic **1.5 pip spread**, the performance crashed to **-2,798R** because the stop-loss was too tight relative to the spread cost (the "Spread Trap").

---

### Phase 2: The Breakthrough — Institutional Trend-Following FVG Model
To resolve the "Spread Trap" and trade alongside institutional momentum, we rebuilt the engine from the ground up:
1. **Trend Definition**: Only take positions in alignment with the major trend (**Fast 50 EMA > Slow 200 EMA** for Longs, and vice versa for Shorts).
2. **Fair Value Gaps (FVG)**: Instead of buying breakout points, we place limit orders to buy/sell when the market pulls back to fill a 3-bar price imbalance (FVG).
3. **High Timeframe Robustness**: By running this strategy on higher timeframes (**H4** and **D1**), the price range of each trade is highly expanded, making a 1.5-pip spread cost negligible.

### 📊 Phase 2 Performance (With 1.5 Pips Spread Included)

Running the upgraded Trend-Following FVG model yielded outstanding profitable returns on higher timeframes:

| Timeframe | Trades Identified | Win Rate | Total Net Return (R) | Status |
| :--- | :---: | :---: | :---: | :---: |
| **D1 (Daily)** | 477 | **38.2%** | **+251.00R** | 🟢 **Highly Profitable** |
| **H4 (4-Hour)** | 1,965 | **27.3%** | **+179.00R** | 🟢 **Highly Profitable** |
| **H1 (1-Hour)** | 6,794 | 22.7% | -626.00R | 🔴 Unprofitable |
| **M15 (15-Min)** | 6,816 | 19.9% | -1,388.00R | 🔴 Unprofitable |

### Key Quantitative Takeaways:
* **Higher Timeframes Win**: On H4 and D1, structural imbalances (FVGs) represent genuine institutional order flow rather than random intraday noise.
* **Spread Immunity**: At a 3.0x Risk-to-Reward ratio on Daily charts, the average trade gain is hundreds of pips, rendering the 1.5-pip spread completely harmless.

---

### Phase 3: Institutional Order Block & Liquidity Sweep Engine
We expanded the strategy suite to combine **Liquidity Sweep Detection** (Turtle Soup sweeps of 20-period swing highs/lows) with **Order Block Mitigation** and **ATR Volatility Stop Protection**:

| Timeframe | Trades Identified | Win Rate | Profit Factor | Net Return (R) | Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **D1 (Daily)** | 188 | **25.5%** | **1.03** | **+4.00R** | 🟢 **Profitable** |
| **H4 (4-Hour)** | 981 | 15.5% | 0.55 | -373.00R | 🔴 Unprofitable |
| **H1 (1-Hour)** | 3,315 | 10.9% | 0.37 | -1,871.00R | 🔴 Unprofitable |
| **M30 (30-Min)** | 3,906 | 10.1% | 0.34 | -2,322.00R | 🔴 Unprofitable |
| **M15 (15-Min)** | 4,203 | 10.8% | 0.36 | -2,387.00R | 🔴 Unprofitable |
| **M5 (5-Min)** | 4,342 | 10.9% | 0.37 | -2,442.00R | 🔴 Unprofitable |

---

## 🚀 How to Run the Backtests

### 1. Requirements
Ensure you have Python 3 and the required data libraries installed:
```bash
pip install pandas numpy matplotlib
```

### 2. Run the PnL Analysis
Run the backtest engine to print the full multi-timeframe FVG analysis:
```bash
python pnl_backtest.py
```

---

## ⚙️ Strategy Configuration & Risk Management Parameters

The backtesting parameters can be customized directly inside `pnl_backtest.py` or `batch_backtest.py`:

| Parameter | Default Value | Description |
| :--- | :---: | :--- |
| `rr_ratio` | `3.0` | Target Risk-to-Reward ratio for take-profit targets |
| `spread_points` | `15` | Simulated transaction cost spread (1.5 pips for XAUUSD) |
| `ema_fast` | `50` | Fast Exponential Moving Average for trend direction filter |
| `ema_slow` | `200` | Slow Exponential Moving Average for long-term trend baseline |

### Recommended Settings for XAUUSD:
- **Daily / 4-Hour Timeframe**: Use `rr_ratio = 3.0` with `spread_points = 15` for optimal risk-adjusted returns.
- **1-Hour Timeframe**: Increase minimum FVG gap height to filter out noise caused by intraday volatility.
