# ICT Turtle Soup Reversal & Liquidity Sweep Backtesting Suite

A professional quantitative trading backtesting engine built to analyze the **ICT Turtle Soup Reversal** (Liquidity Sweep) strategy on Gold (XAUUSD) across multiple timeframes. 

This repository demonstrates the critical difference between theoretical trading strategy performance and realistic market conditions (incorporating bid-ask spreads, transaction costs, and active trading sessions).

---

## 📈 Strategy Concept: Turtle Soup Reversal
The **Turtle Soup** strategy is a classic Smart Money / ICT concept focused on identifying high-probability reversals by trading the failure of breakout traders:
1. **Liquidity Sweep**: Price breaches a recent 20-period swing high or low, triggering stop-orders (liquidity).
2. **Reversal Confirmation**: Price fails to sustain the breakout and closes back inside the previous range (within the same bar).
3. **Execution**: A counter-trend position is entered immediately on the close of the bar, with the stop loss set at the swing high/low extreme and a 2.0x Risk-to-Reward (R) ratio.

---

## 📁 Repository Structure
* `pnl_backtest.py` - The main, highly realistic multi-timeframe backtesting script with session filters and custom spread settings.
* `backtest_ict.py` - Single-file visualization script showing precise entry and exit setups on charts.
* `batch_backtest.py` - Batch processing script to quickly parse multiple market CSV files.
* `ICT_Turtle_Soup.pine` - Production-ready TradingView Pine Script (v5) containing the strategy and dynamic breakeven stop management.
* `csv files/` - Folder containing historical XAUUSD data from `M1` up to `D1` timeframes.

---

## 🔬 The Quantitative Discovery: Theoretical vs. Realistic Performance

Our backtests revealed a fascinating and realistic trading insight. When evaluated without transaction costs and time constraints, the strategy appears to be a "money printer." However, introducing real-world parameters shows how fragile high-frequency patterns can be.

### 1. Theoretical Performance (No Spread, No Session Limit)
*Executing trades 24/7 with zero transaction fees:*

| Timeframe | Trades Identified | Win Rate | Total Return (R) |
| :--- | :---: | :---: | :---: |
| **M1** | 10,940 | 39.1% | **+1,897.00R** |
| **M5** | 11,416 | 37.3% | **+1,343.00R** |
| **M15** | 11,223 | 37.4% | **+1,371.00R** |
| **H1** | 9,042 | 37.3% | **+1,080.00R** |

### 2. Realistic Performance (1.5 Pips Spread + London & NY Session Limits)
*Executing trades only during high-liquidity hours (02:00 - 12:00 EST) and paying a standard 1.5 pip spread:*

| Timeframe | Trades Identified | Win Rate | Total Return (R) |
| :--- | :---: | :---: | :---: |
| **M1** | 4,295 | 10.0% | **-3,008.00R** |
| **M5** | 4,747 | 17.0% | **-2,326.00R** |
| **M15** | 4,970 | 14.6% | **-2,798.00R** |
| **H1** | 3,469 | 18.1% | **-1,585.00R** |

### Key Takeaways for Quant Traders:
1. **The Spread Penalty**: Because the average risk (distance between close and candle low/high) is extremely small on M1, M5, and M15 timeframes, a standard **1.5 pip spread** heavily distorts the risk-to-reward ratio. In many cases, the spread is larger than the actual trade risk, completely wiping out the edge.
2. **Session Realism**: Restricting trades to the highly volatile London and NY sessions prevents trading during flat range-bound Asian/rollover sessions, but also filters out many false breakout consolidations that the strategy previously "survived."

---

## 🚀 How to Run the Backtests

### 1. Requirements
Ensure you have Python 3 and the required data libraries installed:
```bash
pip install pandas numpy matplotlib
```

### 2. Run the realistic PnL Analysis
Evaluate the strategy across all timeframes with configurable spreads and session filters:
```bash
python pnl_backtest.py
```

### 3. Run the visual backtest on specific datasets
View the plot of entries and exits (if any meet the strict FVG criteria):
```bash
python backtest_ict.py XAU_15m_data.csv
```
