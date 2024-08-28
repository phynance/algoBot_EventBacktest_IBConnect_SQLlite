import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
import requests
from performance import *

#print(plt.style.available)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 10)

plt.style.use('seaborn-v0_8')
mpl.rcParams['font.family'] = 'serif'


class BacktestBase(object):
    # TODO data fetch migration, accepting numerous symbols,
    def __init__(self, symbol, start, end, cash, commission_included=False, verbose=True):
        self.data = None
        self.symbol = symbol
        self.start = start
        self.end = end
        self.initial_amount = cash
        self.cash = cash
        self.commission = 0
        self.units = 0
        self.position = 0
        self.trades = 0
        self.commission_included = commission_included
        self.verbose = verbose
        self.get_data()  # lead to a new dataframe: self.data
        self.tradeRecord = pd.DataFrame(columns=['units', 'price'])


    def get_data(self):
        """ Retrieves and prepares the data. """
        file_path = '../data/pyalgo_eikon_eod_data.csv'
        if os.path.isfile(file_path):
            raw = pd.read_csv(file_path, index_col=0, parse_dates=True).dropna()
        else:
            response = requests.get('http://hilpisch.com/pyalgo_eikon_eod_data.csv')
            with open(file_path, 'wb') as file:
                file.write(response.content)
            raw = pd.read_csv(file_path, index_col=0, parse_dates=True).dropna()

        raw = pd.DataFrame(raw[self.symbol])
        raw = raw.loc[self.start:self.end]
        #raw.rename(columns={self.symbol: 'price'}, inplace=True)
        #raw['return'] = np.log(raw / raw.shift(1))

        self.data = raw.dropna()
        self.data.loc[:, ['units', 'cash', 'net_wealth']] = None  # initialize 3 more columns

    def get_date_price(self, bar):
        ''' Return date and price for bar.'''
        date = self.data.index[bar]
        price = self.data[self.symbol].iloc[bar]
        return date, price

    def print_balance(self, bar):
        ''' Print out current cash balance info.'''
        date, price = self.get_date_price(bar)
        print(f'{str(date)[:10]} | current balance {self.cash:.2f}')

    def calculate_commission(self, num_shares, price_per_share):
        # Define commission rate and limits
        commission_rate = 0.0035
        min_commission = 0.35
        max_commission_percentage = 0.01
        basic_commission = num_shares * commission_rate
        trade_value = num_shares * price_per_share
        max_commission = trade_value * max_commission_percentage
        commission = max(min_commission, min(basic_commission, max_commission))
        return commission

    def place_buy_order(self, bar, units=None, cash=None):
        # TODO save the buying date and price
        ''' Place a buy order. '''
        date, price = self.get_date_price(bar)
        #self.buydates.append(bar)
        if units is None:
            units = int(cash / price)

        self.tradeRecord.loc[date] = [units, price]
        if self.commission_included:
            self.commission = self.calculate_commission(units, price)
        else:
            self.commission = 0

        self.cash -= (units * price) + self.commission
        self.units += units
        self.trades += 1
        if self.verbose:
            print(f'{str(date)[:10]} | buying {units} units at {price:.2f} ')
            self.print_balance(bar)
        #self.data.loc[self.data.index[bar], 'units'] = self.units  # store in the df ###########

    def place_sell_order(self, bar, units=None, cash=None):
        # TODO save the selling date and price
        ''' Place a sell order.'''
        date, price = self.get_date_price(bar)
        #self.selldates.append(bar)
        if units is None:
            units = int(cash / price)
        self.tradeRecord.loc[date] = [-units, price]

        if self.commission_included:
            self.commission = self.calculate_commission(units, price)
        else:
            self.commission = 0

        self.cash += (units * price) - self.commission  #cash out
        self.units -= units
        self.trades += 1
        if self.verbose:
            print(f'{str(date)[:10]} | selling {units} units at {price:.2f} ')
            self.print_balance(bar)
        #self.data.loc[self.data.index[bar], 'units'] = self.units  # store in the df ###########

    def close_out(self, bar):
        ''' Closing out a long or short position.'''
        date, price = self.get_date_price(bar)
        self.cash += self.units * price
        self.units = 0
        self.trades += 1
        if self.verbose:
            print(f'{str(date)[:10]} | inventory {self.units} units at {price:.2f}')
            print('=' * 55)
        print('Final balance   [$] {:.2f}'.format(self.cash))
        # perf = ((self.cash - self.initial_amount) /
        #         self.initial_amount * 100)
        # print('Net Performance [%] {:.2f}'.format(perf))
        print('Trades Executed [#] {:.2f}'.format(self.trades))
        print('=' * 55)


    def plot_data(self):
        """ Plots the closing prices for symbol."""
        plt.figure(1)
        plt.subplot(2, 1, 1)
        plt.plot(self.data.index, self.data[self.symbol], linewidth=1., label='Stock Price')

        #self.data[self.symbol].plot(title=self.symbol, linewidth=1., label='stock price')

        long_dates = []
        long_prices = []

        for date, row in self.tradeRecord.iterrows():
            if row['units'] > 0:
                plt.plot(date, row['price'], '^', markersize=5, color='g', label='Long')
            elif row['units'] < 0:
                plt.plot(date, row['price'], 'v', markersize=5, color='r', label='short')

        plt.subplot(2, 1, 2)
        self.data['equity_curve'].plot(title="Equity curve", color='#FFAF33')

        plt.subplots_adjust(left=0.1,
                            bottom=0.1,
                            right=0.9,
                            top=0.9,
                            wspace=0.4,
                            hspace=0.6)
        plt.show()

    def summary_stats(self):
        # TODO   CAGR, Information Ratio, , Sortino, winning rate

        self.data = create_equity_curve_dataframe(self.data)
        total_return = self.data['equity_curve'].iloc[-1]
        sharpe_ratio = calculate_sharpe_ratio(self.data['returns'])
        max_dd, dd_duration = calculate_drawdowns(self.data['equity_curve'])
        calmar_ratio = calculate_calmar_ratio(self.data['equity_curve'])

        stats = [("Total Return", "%0.2f%%" % ((total_return - 1.0) * 100.0)),
                 ("Sharpe Ratio", "%0.2f" % sharpe_ratio),
                 ("Calmar Ratio", "%0.2f" % calmar_ratio),
                 ("Max Drawdown", "%0.2f%%" % (max_dd * 100.0)),
                 ("Drawdown Duration", "%d" % dd_duration)]

        for stat in stats:
            print(f"{stat[0]}: {stat[1]}")
