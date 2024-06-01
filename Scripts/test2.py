from contextlib import contextmanager
import ib_insync
from IBconnect.TradeAPI import AbstractTradeInterface
from datetime import datetime, timedelta
import math
from zoneinfo import ZoneInfo


class InteractiveBrokerTradeAPI(AbstractTradeInterface):
    def __init__(self, currency='USD'):
        self.client = None
        self.accounts = []
        self.currency = currency
        self.timezone = ZoneInfo('US/Eastern')

    @contextmanager
    def connect(self):
        self.client = ib_insync.IB()
        # Newly added
        self.client.orderStatusEvent += self.__order_status
        self.client.connect('127.0.0.1', 7497, 101)
        print("=" * 30)
        print("Connection established")
        print("=" * 30)

        yield self

        self.client.disconnect()
        self.client.sleep(2)
        print("=" * 30)
        print("Connection closed")
        print("=" * 30)

    def get_account_detail(self):
        self.accounts = self.client.managedAccounts()

        acc_data = []
        for account in self.accounts:
            acc = {}
            acc['account'] = account
            data = self.client.accountValues(account)
            acc['cash'] = 0
            acc['total_assets'] = 0
            for row in data:
                if row.tag in ['TotalCashBalance'] and row.currency == self.currency:
                    acc['cash'] = row.value
                    acc['total_assets'] += float(row.value)
                elif row.tag in ['StockMarketValue'] and row.currency == self.currency:
                    acc['total_assets'] += float(row.value)
            acc_data.append(acc)

        pos_data = []
        data = self.client.portfolio()
        for position in data:
            pos = {}

            pos['code'] = position.contract.symbol
            pos['qty'] = position.position
            pos['cost_price'] = position.averageCost
            pos['market_val'] = position.marketValue
            pos['pl_val'] = position.unrealizedPNL
            if pos['cost_price'] * pos['qty'] == 0:
                pos['pl_ratio'] = 0
            else:
                pos['pl_ratio'] = pos['pl_val'] / (pos['cost_price'] * pos['qty'])
            pos_data.append(pos)

        orders_data = []
        data = self.client.trades()
        for order in data:
            print(order)
            o = {}
            o['order_id'] = order.order.permId
            o['order_status'] = order.orderStatus.status
            o['create_time'] = order.log[-1].time if order.log else None  # order.log[-1].time
            o['trd_side'] = order.order.action
            o['order_type'] = order.order.action
            o['code'] = order.contract.symbol
            orders_data.append(o)
        return acc_data, pos_data, orders_data

    def place_order(self, symbol: str, quantity: int, price: float = 0):
        contract = ib_insync.Stock(symbol.upper(), 'SMART', self.currency)
        self.client.qualifyContracts(contract)
        if quantity >= 0.0:
            order = ib_insync.MarketOrder('BUY', quantity)
        else:
            order = ib_insync.MarketOrder('SELL', -quantity)
        trade = self.client.placeOrder(contract, order)
        self.client.sleep(5)

        return True

    def get_last_price_from_quote(self, symbol: str):
        contract = ib_insync.Stock(symbol.upper(), 'SMART', self.currency)
        # self.client.reqMarketDataType(3)
        self.client.reqMarketDataType(3)
        self.client.qualifyContracts(contract)
        quote = self.client.reqMktData(
            contract,
            genericTickList="",
            snapshot=True,
            regulatorySnapshot=False,
            mktDataOptions=None
        )

        for _ in range(10):
            if math.isnan(quote.last):
                self.client.sleep(1)
            else:
                return quote.last
        print(f'No last price in quote for {symbol}')
        return 0

    def __order_status(self, trade):
        '''
        Call back function for checking order status
        '''
        print(f'Order [{trade.contract.symbol}] status updated: {trade.orderStatus.status}')
        match trade.orderStatus.status:
            case 'Filled':
                print(f'Order {trade.contract.symbol}, filled.')
            case _:
                print(f'Others order status: {trade.orderStatus.status}')

    def is_market_open(self, offset_days=0):
        spy_contract = ib_insync.Stock('SPY', 'SMART', self.currency)
        self.client.qualifyContracts(spy_contract)
        trading_days = self.client.reqContractDetails(spy_contract)[0].liquidHours
        trading_days_dict = {d.split(':')[0]: d.split(':')[1] for d in trading_days.split(';')}
        print(trading_days_dict)

        today_str = (datetime.now().astimezone(self.timezone) + timedelta(days=offset_days)).strftime('%Y%m%d')

        for k, v in trading_days_dict.items():
            if (today_str in k) and (v == 'CLOSED'):
                return False

        return True

    def is_market_open_now(self):
        spy_contract = ib_insync.Stock('SPY', 'SMART', self.currency)
        self.client.qualifyContracts(spy_contract)
        trading_days = self.client.reqContractDetails(spy_contract)[0].liquidHours
        trading_days_list = [d.split('-') for d in trading_days.split(';')]
        print(trading_days_list)

        day_str = datetime.now().astimezone(self.timezone).strftime('%Y%m%d')
        time_str = datetime.now().astimezone(self.timezone).strftime('%H%M')

        for d in trading_days_list:
            if len(d) > 1 and day_str in d[0].split()[0]:
                if time_str > d[0].split(':')[1] and time_str < d[1].split(':')[1]:
                    return True

        return False

    def get_transactions(self):
        pass


# Main function
if __name__ == '__main__':
    broker = InteractiveBrokerTradeAPI()
    print(datetime.now().strftime('Now is %Y-%m-%d'))
    with broker.connect() as c:
        accounts, positions, orders = c.get_account_detail()
        print(ib_insync.util.df(accounts))
        print(ib_insync.util.df(positions))
        print(ib_insync.util.df(orders))
        print("=" * 30)
        market_open = c.is_market_open()
        market_open_now = c.is_market_open_now()
        print(f'{market_open=}')
        print(f'{market_open_now=}')
        print("=" * 30)
        print(c.get_last_price_from_quote('SSO'))
        if market_open and market_open_now:
            last = c.get_last_price_from_quote('AAPL')
            print(f'{last=}')
            c.place_order('AAPL', 1)
