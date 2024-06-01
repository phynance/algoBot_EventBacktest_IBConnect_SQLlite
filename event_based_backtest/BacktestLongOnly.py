from BacktestBase import *


class BacktestLongOnly(BacktestBase):

    def run_sma_strategy(self, SMA1, SMA2):
        ''' Backtesting a SMA-based strategy.

        Parameters
        ==========
        SMA1, SMA2: int
            shorter and longer term simple moving average (in days)
        '''
        msg = f'\n\nRunning SMA strategy | SMA1={SMA1} & SMA2={SMA2}'
        msg += f'\nfixed costs {self.ftc} | '
        msg += f'proportional costs {self.ptc}'
        print(msg)
        print('=' * 55)
        self.position = 0  # initial neutral position
        self.trades = 0  # no trades yet
        self.amount = self.initial_amount  # reset initial capital
        self.data['SMA1'] = self.data['price'].rolling(SMA1).mean()
        self.data['SMA2'] = self.data['price'].rolling(SMA2).mean()
        self.data.iloc[:SMA2, self.data.columns.get_loc('net_wealth')] = self.amount  # initialize the first SMA2 days are with amount dollars

        for bar in range(SMA2, len(self.data)):
            date, price = self.get_date_price(bar)
            if self.position == 0:
                if self.data['SMA1'].iloc[bar] > self.data['SMA2'].iloc[bar]:
                    self.place_buy_order(bar, amount=self.amount)  # buy amount
                    self.position = 1  # long position
            elif self.position == 1:
                if self.data['SMA1'].iloc[bar] < self.data['SMA2'].iloc[bar]:
                    self.place_sell_order(bar, units=self.units)  # sell units
                    self.position = 0  # market neutral

            self.data.loc[self.data.index[bar], 'units'] = self.units  # store in the df ###########
            self.data.loc[self.data.index[bar], 'position'] = self.position  # store in the df ###########
            self.data.loc[self.data.index[bar], 'amount'] = self.amount
            self.data.loc[self.data.index[bar], 'net_wealth'] = self.units * price + self.amount  # store in the df ##########
        self.close_out(bar)

    # def run_momentum_strategy(self, momentum):
    #     ''' Backtesting a momentum-based strategy.
    #
    #     Parameters
    #     ==========
    #     momentum: int
    #         number of days for mean return calculation
    #     '''
    #     msg = f'\n\nRunning momentum strategy | {momentum} days'
    #     msg += f'\nfixed costs {self.ftc} | '
    #     msg += f'proportional costs {self.ptc}'
    #     print(msg)
    #     print('=' * 55)
    #     self.position = 0  # initial neutral position
    #     self.trades = 0  # no trades yet
    #     self.amount = self.initial_amount  # reset initial capital
    #     self.data['momentum'] = self.data['return'].rolling(momentum).mean()  # moving average of daily return
    #     for bar in range(momentum, len(self.data)):
    #         if self.position == 0:
    #             if self.data['momentum'].iloc[bar] > 0:
    #                 self.place_buy_order(bar, amount=self.amount)
    #                 self.position = 1  # long position
    #         elif self.position == 1:
    #             if self.data['momentum'].iloc[bar] < 0:
    #                 self.place_sell_order(bar, units=self.units)
    #                 self.position = 0  # market neutral
    #     self.close_out(bar)
    #
    # def run_mean_reversion_strategy(self, SMA, threshold):
    #     ''' Backtesting a mean reversion-based strategy.
    #
    #     Parameters
    #     ==========
    #     SMA: int
    #         simple moving average in days
    #     threshold: float
    #         absolute value for deviation-based signal relative to SMA
    #     '''
    #     msg = f'\n\nRunning mean reversion strategy | '
    #     msg += f'SMA={SMA} & thr={threshold}'
    #     msg += f'\nfixed costs {self.ftc} | '
    #     msg += f'proportional costs {self.ptc}'
    #     print(msg)
    #     print('=' * 55)
    #     self.position = 0
    #     self.trades = 0
    #     self.amount = self.initial_amount
    #
    #     self.data['SMA'] = self.data['price'].rolling(SMA).mean()  # moving average
    #
    #     for bar in range(SMA, len(self.data)):
    #         if self.position == 0:
    #             if (self.data['price'].iloc[bar] <
    #                     self.data['SMA'].iloc[bar] - threshold):
    #                 self.place_buy_order(bar, amount=self.amount)
    #                 self.position = 1
    #         elif self.position == 1:
    #             if self.data['price'].iloc[bar] >= self.data['SMA'].iloc[bar]:
    #                 self.place_sell_order(bar, units=self.units)
    #                 self.position = 0
    #     self.close_out(bar)


if __name__ == '__main__':
    def run_strategies(BL):
        BL.run_sma_strategy(42, 252)
        #BL.run_momentum_strategy(60)
        #BL.run_mean_reversion_strategy(50, 5)


    lobt = BacktestLongOnly('AAPL.O', '2010-1-1', '2019-12-31', 10000, verbose=True)
    run_strategies(lobt)
    #print(lobt.data.iloc[650:750])
    print(lobt.buydates)
    lobt.plot_data()

    # transaction costs: 10 USD fix, 1% variable
    lobt = BacktestLongOnly('AAPL.O', '2010-1-1', '2019-12-31', 10000,
                            10.0, 0.01, False)
    #run_strategies(lobt)
