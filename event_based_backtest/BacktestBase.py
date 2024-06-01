import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
import requests

#print(plt.style.available)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

plt.style.use('seaborn-v0_8')
mpl.rcParams['font.family'] = 'serif'


class BacktestBase(object):
    """ Base class for event-based backtesting of trading strategies.
    Attributes
    ==========
        symbol: str
            TR RIC (financial instrument) to be used
        start: str
            start date for data selection
        end: str
            end date for data selection
        amount: float
            amount to be invested either once or per trade
        ftc: float
            fixed transaction costs per trade (buy or sell)
        ptc: float
            proportional transaction costs per trade (buy or sell)
    Methods     =======
        get_data:
            retrieves and prepares the base data set
        plot_data:
            plots the closing price for the symbol
        get_date_price:
            returns the date and price for the given bar
        print_balance:
            prints out the current (cash) balance
        print_net_wealth:
            prints out the current net wealth
        place_buy_order:
            places a buy order
        place_sell_order:
            places a sell order
        close_out:
            closes out a long or short position
    """

    def __init__(self, symbol, start, end, amount, ftc=0.0, ptc=0.0, verbose=True):
        self.data = None
        self.symbol = symbol
        self.start = start
        self.end = end
        self.initial_amount = amount
        self.amount = amount
        self.ftc = ftc
        self.ptc = ptc
        self.units = 0
        self.position = 0
        self.trades = 0
        self.verbose = verbose
        self.get_data()  # lead to a new dataframe: self.data
        self.buydates = []
        self.selldates = []
        #self.data = pd.DataFrame()

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
        raw.rename(columns={self.symbol: 'price'}, inplace=True)
        raw['return'] = np.log(raw / raw.shift(1))

        self.data = raw.dropna()
        self.data.loc[:, ['position', 'units', 'net_wealth', 'amount']] = None  # initialize 3 more columns

    def get_date_price(self, bar):
        ''' Return date and price for bar.'''
        date = str(self.data.index[bar])[:10]
        price = self.data.price.iloc[bar]
        return date, price

    def print_balance(self, bar):
        ''' Print out current cash balance info.'''
        date, price = self.get_date_price(bar)
        print(f'{date} | current balance {self.amount:.2f}')

    def print_net_wealth(self, bar):
        ''' Print out current cash balance info. '''

        date, price = self.get_date_price(bar)
        net_wealth = self.units * price + self.amount
        print(f'{date} | current net wealth {net_wealth:.2f}')

    def place_buy_order(self, bar, units=None, amount=None):
        # TODO save the buying date and price
        ''' Place a buy order. '''
        date, price = self.get_date_price(bar)
        self.buydates.append(bar)
        if units is None:
            units = int(amount / price)
        self.amount -= (units * price) * (1 + self.ptc) + self.ftc
        self.units += units
        self.trades += 1
        if self.verbose:
            print(f'{date} | buying {units} units at {price:.2f} ')
            self.print_balance(bar)
        self.print_net_wealth(bar)
        #self.data.loc[self.data.index[bar], 'units'] = self.units  # store in the df ###########

    def place_sell_order(self, bar, units=None, amount=None):
        # TODO save the selling date and price
        ''' Place a sell order.'''
        date, price = self.get_date_price(bar)
        self.selldates.append(bar)
        if units is None:
            units = int(amount / price)
        self.amount += (units * price) * (1 - self.ptc) - self.ftc
        self.units -= units
        self.trades += 1
        if self.verbose:
            print(f'{date} | selling {units} units at {price:.2f} ')
            self.print_balance(bar)
        self.print_net_wealth(bar)
        #self.data.loc[self.data.index[bar], 'units'] = self.units  # store in the df ###########

    def close_out(self, bar):
        ''' Closing out a long or short position.'''
        date, price = self.get_date_price(bar)
        self.amount += self.units * price
        self.units = 0
        self.trades += 1
        if self.verbose:
            print(f'{date} | inventory {self.units} units at {price:.2f}')
            print('=' * 55)
        print('Final balance   [$] {:.2f}'.format(self.amount))
        perf = ((self.amount - self.initial_amount) /
                self.initial_amount * 100)
        print('Net Performance [%] {:.2f}'.format(perf))
        print('Trades Executed [#] {:.2f}'.format(self.trades))
        print('=' * 55)

    #TODO equity curve, sharpe ratio, CAGR, Information Ratio, Calamr, Sortino, MMD, winning rate

    def plot_data(self):
        """ Plots the closing prices for symbol."""
        # TODO plot the equity curve & chart showing buying & selling dates
        plt.figure(1)
        plt.subplot(2,1,1)
        self.data['price'].plot(title=self.symbol, linewidth=1., label='stock price')

        for pos in self.buydates:
            """ add green dot for buy dates """
            plt.plot(self.data.index[pos], self.data.price.iloc[pos], 'go', markersize=5, label='buy')

        for pos in self.selldates:
            """ add green dot for sell dates """
            plt.plot(self.data.index[pos], self.data.price.iloc[pos], 'ro', markersize=5, label='sell')

        plt.subplot(2,1,2)
        self.data['net_wealth'].plot(title="Equity curve", color='#FFAF33')

        plt.subplots_adjust(left=0.1,
                            bottom=0.1,
                            right=0.9,
                            top=0.9,
                            wspace=0.4,
                            hspace=0.6)
        plt.show()


if __name__ == '__main__':
    bb = BacktestBase('AAPL.O', '2010-1-1', '2019-12-31', 10000)
    dftest = bb.data
    print(dftest.info())
    #print(dftest.iloc[0:750])
    #bb.plot_data(['price','net_wealth'])
