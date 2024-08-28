# Algorithmic Trading Bot

This project is an algorithmic trading bot implemented in Python, designed for event-based backtesting. It includes various trading strategies such as long/short strategies, momentum strategies, and mean reversion strategies.

## Features

- **Event-Based Backtesting**: Simulate trading strategies using historical data.
- **Multiple Trading Strategies**:
  - **Long/Short Strategy**: Execute trades based on Simple Moving Averages (SMA).
  - **Momentum Strategy**: Trade based on recent price momentum.
  - **Mean Reversion Strategy**: Trade based on the deviation from a moving average.
- **Transaction Cost Management**: Incorporate fixed and variable transaction costs.

## Requirements

- Python 3.9
- `pandas`
- `numpy`
- `BacktestBase` class (provided in the project)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/phynance/algoBot_EventBacktest_IBConnect_SQLlite.git
