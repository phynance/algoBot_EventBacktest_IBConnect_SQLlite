import numpy as np
import pandas as pd
import statsmodels.tsa.vector_ar.vecm as vm
from datetime import datetime
from data.yfinance_dataFetch import StockDataFetcher
import matplotlib.pyplot as plt
import os

# Load or fetch S&P 500 closing prices
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
#file_path = os.path.join(parent_dir, sp500_file)

sp500_file = os.path.join(parent_dir, 'data/sp500_closing_prices_last_10_years.csv')
spy_file = os.path.join(parent_dir, 'data/SPY_last_10_years.csv')


parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sp500_file = os.path.join(parent_dir, 'data/sp500_closing_prices_last_10_years.csv')
spy_file = os.path.join(parent_dir, 'data/SPY_last_10_years.csv')

if os.path.exists(sp500_file):
    cl = pd.read_csv(sp500_file)
else:
    fetcher = StockDataFetcher(start_date="2014-01-01", end_date=datetime.now())
    closing_prices = fetcher.fetch_data()
    fetcher.save_to_csv(closing_prices, sp500_file)
    cl = closing_prices

all_nan_columns = cl.columns[cl.isna().all()].tolist()
# Remove columns with all NaN values
cl = cl.drop(columns=all_nan_columns)
cl['Date'] = pd.to_datetime(cl['Date'], format='%Y-%m-%d').dt.date
cl.set_index('Date', inplace=True)

# ETFs
if os.path.exists(spy_file):
    cl_etf = pd.read_csv(spy_file)
else:
    fetcher = StockDataFetcher(start_date="2014-01-01", end_date=datetime.now(), symbols=["SPY"])
    closing_prices = fetcher.fetch_data()
    fetcher.save_to_csv(closing_prices, spy_file)
    cl_etf = closing_prices

cl_etf['Date'] = pd.to_datetime(cl_etf['Date'], format='%Y-%m-%d').dt.date  # change the 1st column to datetime format
#cl_etf.columns=np.insert(etfs.values, 0, 'Date')
cl_etf.set_index('Date', inplace=True)
#cl_etf = cl_etf[['SPY']]

# Merge on common dates
df = pd.merge(cl, cl_etf, how='inner', on='Date')  #502 stocks + 1 SPY

cl_stocks = df[cl.columns]  # stocks on only common dates
cl_etf = df[cl_etf.columns]  # etf on only common dates

# Use SPY only
cl_etf = cl_etf['SPY']  # This turns cl_etf into Series

#251 days
year = 2020
trainDataIdx = df.index[(df.index > datetime(2014, 1, 1).date()) & (df.index <= datetime(year, 12, 31).date())]
testDataIdx = df.index[df.index > datetime(year, 12, 31).date()]

isCoint = np.full(cl_stocks.shape[1], False)

for s in range(cl_stocks.shape[1]):
    """ what if the stock is not in SPX within that training period? """
    # Combine the two time series into a matrix y2 for input into Johansen test
    y2 = pd.concat([cl_stocks.loc[trainDataIdx].iloc[:, s], cl_etf.loc[trainDataIdx]], axis=1)
    y2 = y2.loc[y2.notnull().all(axis=1),]  #filter out rows(dates) that contain any null
    if y2.shape[0] <= 250*7:
        print(f"{cl_stocks.columns[s]} does not have right data")
    elif y2.shape[0] > 250*7:  # if not enough data, then take it as non-cointegrated
        # Johansen test
        result = vm.coint_johansen(y2.values, det_order=0, k_ar_diff=1)
        if result.lr1[0] > result.cvt[0, 1]:  # 95%
            isCoint[s] = True

print(f"number of cointegrating stocks: {isCoint.sum()}")

yN = cl_stocks.loc[trainDataIdx, isCoint]  # filter out the cointegrated stocks
logMktVal_long = np.sum(np.log(yN), axis=1)  # The net market value of the long-only portfolio is same as the "spread"

# Confirm that the portfolio in training period cointegrates with SPY
ytest = pd.concat([logMktVal_long, np.log(cl_etf.loc[trainDataIdx])], axis=1)

result = vm.coint_johansen(ytest, det_order=0, k_ar_diff=1)
print(f"Trace Statistics (lr1):\n{result.lr1}\n")
print(f"Critical Values for Trace Statistic (cvt):\n{result.cvt}\n")
print(f"Maximum Eigenvalue Statistics (lr2):\n{result.lr2}\n")
print(f"Critical Values for Maximum Eigenvalue Statistic (cvm):\n{result.cvm}\n")
print(f"Eigenvector(evec):\n{result.evec}\n")


#Apply linear mean-reversion model on test set
yNplus = pd.concat([cl_stocks.loc[testDataIdx, isCoint], pd.DataFrame(cl_etf.loc[testDataIdx])],axis=1)
# Array of stock and ETF prices
# Create an array of weights using eigenvectors from Johansen cointegration test results
weights = np.column_stack((
    np.full((testDataIdx.shape[0], isCoint.sum()), result.evec[0, 0]),
    np.full((testDataIdx.shape[0], 1), result.evec[1, 0])
))

# key step, applying same weights on cointegrated stock
cointstocks_spy = weights * np.log(yNplus)
cointstocks_spy['combinedStocks_weighted'] = cointstocks_spy.iloc[:, 0:-1].sum(axis=1)
new_df = cointstocks_spy[['combinedStocks_weighted', 'SPY']]
new_df.columns = ['combinedStocks_weighted', 'SPY_weighted']


####################################################################################

# Plot the series
plt.figure(figsize=(12, 6))
plt.plot(new_df.index, new_df['combinedStocks_weighted'], label='combinedStocks_weighted')
plt.plot(new_df.index, -1*new_df['SPY_weighted'], label='SPY_weighted')
plt.title('weighted portfolio & weighted SPY')
plt.xlabel('date')
plt.ylabel('Value')
plt.legend()
plt.show(block=False)

####################################################################################
plt.figure(figsize=(12,6))
plt.plot(new_df.index, new_df['combinedStocks_weighted']+ new_df['SPY_weighted'], label='spread')
plt.title('spread between weighted portfolio & weighted SPY')
plt.xlabel('date')
plt.ylabel('Value')
plt.legend()
plt.show(block=False)

####################################################################################
lookback = 5
logMktVal = np.sum(new_df, axis=1)  # Log market value of long-short portfolio
numUnits = -(logMktVal - logMktVal.rolling(lookback).mean()) / logMktVal.rolling(lookback).std()
# capital invested in portfolio in dollars.  movingAvg and movingStd are functions from epchan.com/book2
positions = pd.DataFrame(np.expand_dims(numUnits, axis=1) * weights)
# results.evec(:, 1)' can be viewed as the capital allocation, while positions is the dollar capital in each ETF.
pnl = np.sum((positions.shift().values) * (np.log(yNplus) - np.log(yNplus.shift()).values), axis=1)  # daily P&L of the strategy
ret = pd.DataFrame(pnl.values / np.sum(np.abs(positions.shift()), axis=1).values)
ret = pd.DataFrame(ret.values, index=pnl.index, columns=['Return'])

#
# Plot the cumulative returns
cumulative_returns = (np.cumprod(1 + ret) - 1)
cumulative_returns.plot()
plt.title('Cumulative Returns')
plt.xlabel('Date')
plt.ylabel('Cumulative Return')
plt.show()

# Calculate and print the APR and Sharpe ratio
APR = np.prod(1 + ret) ** (252 / len(ret)) - 1
Sharpe = np.sqrt(252) * np.mean(ret) / np.std(ret)
print('APR=%f Sharpe=%f' % (APR, Sharpe))
