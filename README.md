# Algorithmic Trading Bot

This project aims to develop a comprehensive algorithmic trading engine that includes an event-driven backtesting framework, performance and risk metrics, and integration with Interactive Brokers for live trading. Additionally, it features an SQLite database to store completed trades, facilitating effective portfolio management.


## Features

- **Event-Based Backtesting**: Simulate trading strategies using historical data.
- **Multiple Trading Strategies**:
  - **Long/Short Strategy**: Execute trades based on Simple Moving Averages (SMA).
  - **Pair Trading**: Trade based on recent price momentum.
- **Transaction Cost Management**: Incorporate fixed and variable transaction costs.
- **Interactive Broker Connection**: This bot can connect to IB paper account or live trading account.
- **SQLite Database**: For better portfolio managment, SQLite database is used to store the transaction and current portfolio details. 

## Requirements

- Python 3.9
- `pandas`
- `numpy`
- `BacktestBase` class (provided in the project)
- ib_insync
- statsmodels
- matplotlib


## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/phynance/algoBot_EventBacktest_IBConnect_SQLlite.git
