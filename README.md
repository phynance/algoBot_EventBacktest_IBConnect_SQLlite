# Algorithmic Trading Bot

This project is an algorithmic trading bot implemented in Python, designed for event-based backtesting. It includes various trading strategies such as long/short strategies, momentum strategies, and mean reversion strategies.

## Work flow 
### 1. Data Fetching:

The historical data is fetched through yfinance library. StockDataFetcher class is initialized with a date range and an optional list of stock symbols. 
In this project, the sample data are attached in the repo `data` so user can directly use the example data set to have a quick start on the trading bot.

### 2. Event-Based Backtesting 

Although vectorized backtesting is efficient and convenient to implement, it is prone to look-ahead bias. Therefore, a more-realistic approach `Event-based Backtesting`. 
The trading signals are only triggered through the arrival of new data.


### 3. Multiple Trading Strategies:
  - **Long/Short Strategy**: Execute trades based on Simple Moving Averages (SMA).
  - **Momentum Strategy**: Trade based on recent price momentum.
  - **Mean Reversion Strategy**: Trade based on the deviation from a moving average.
  - 
Simulate trading strategies using historical data.
**Transaction Cost Management**: Incorporate fixed and variable transaction costs.

### 4. Paper/ Live trading


### 5. Database setup to store portfolio history

- ****: 

- 


## QuickStart
To have a better understanding on the workflow and features of this trading bot, user can first try to run the `SMAsCross_QuickStart` in `event_based_backtest`.

![Signals_EquityCurve.png](Signals_EquityCurve.png)

======================================================= \
Final balance   [\$] 47074.72 \
Trades Executed [\#] 68.00 \
======================================================= \

Total Return: 370.75% \
Sharpe Ratio: 0.91 \
Calmar Ratio: 0.30 \
Max Drawdown: 55.33% \
Drawdown Duration: 495

## Requirements

- Python 3.9
- `pandas`
- `numpy`
- ib_insync

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/phynance/algoBot_EventBacktest_IBConnect_SQLlite.git


## Further development:
Websocket to extract real-time data for higher frequency trading
