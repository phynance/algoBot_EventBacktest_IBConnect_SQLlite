from contextlib import contextmanager
import ib_insync
from IBconnect.TradeAPI_interface import AbstractTradeInterface
from datetime import datetime, timedelta
import math
from zoneinfo import ZoneInfo

class BrokerAPI(AbstractTradeInterface):
    def __init__(self, default_currency='USD'):
        self.api_client = None
        self.user_accounts = []
        self.default_currency = default_currency
        self.local_timezone = ZoneInfo('US/Eastern')

    @contextmanager
    def establish_connection(self):
        self.api_client = ib_insync.IB()
        self.api_client.orderStatusEvent += self.__handle_order_status
        self.api_client.connect('127.0.0.1', 7497, 101)
        print("=" * 30)
        print("Connected to the API")
        print("=" * 30)

        yield self

        self.api_client.disconnect()
        self.api_client.sleep(2)
        print("=" * 30)
        print("Disconnected from the API")
        print("=" * 30)

    def retrieve_account_info(self):
        self.user_accounts = self.api_client.managedAccounts()

        account_details = []
        for account in self.user_accounts:
            account_info = {}
            account_info['account_id'] = account
            data = self.api_client.accountValues(account)
            account_info['available_cash'] = 0
            account_info['total_value'] = 0
            for entry in data:
                if entry.tag in ['TotalCashBalance'] and entry.currency == self.default_currency:
                    account_info['available_cash'] = entry.value
                    account_info['total_value'] += float(entry.value)
                elif entry.tag in ['StockMarketValue'] and entry.currency == self.default_currency:
                    account_info['total_value'] += float(entry.value)
            account_details.append(account_info)

        position_details = []
        portfolio_data = self.api_client.portfolio()
        for pos in portfolio_data:
            position_info = {}

            position_info['ticker'] = pos.contract.symbol
            position_info['quantity'] = pos.position
            position_info['average_cost'] = pos.averageCost
            position_info['market_value'] = pos.marketValue
            position_info['unrealized_pnl'] = pos.unrealizedPNL
            if position_info['average_cost'] * position_info['quantity'] == 0:
                position_info['pnl_ratio'] = 0
            else:
                position_info['pnl_ratio'] = position_info['unrealized_pnl'] / (position_info['average_cost'] * position_info['quantity'])
            position_details.append(position_info)

        order_details = []
        trades = self.api_client.trades()
        for trade in trades:
            print(trade)
            order_info = {}
            order_info['id'] = trade.order.permId
            order_info['status'] = trade.orderStatus.status
            order_info['timestamp'] = trade.log[-1].time if trade.log else None
            order_info['side'] = trade.order.action
            order_info['type'] = trade.order.action
            order_info['ticker'] = trade.contract.symbol
            order_details.append(order_info)
        return account_details, position_details, order_details

    def submit_order(self, ticker: str, qty: int, limit_price: float = 0):
        stock_contract = ib_insync.Stock(ticker.upper(), 'SMART', self.default_currency)
        self.api_client.qualifyContracts(stock_contract)
        if qty >= 0:
            order = ib_insync.MarketOrder('BUY', qty)
        else:
            order = ib_insync.MarketOrder('SELL', -qty)
        self.api_client.placeOrder(stock_contract, order)
        self.api_client.sleep(5)

        return True

    def fetch_last_price(self, ticker: str):
        stock_contract = ib_insync.Stock(ticker.upper(), 'SMART', self.default_currency)
        self.api_client.reqMarketDataType(3)
        self.api_client.qualifyContracts(stock_contract)
        market_quote = self.api_client.reqMktData(
            stock_contract,
            genericTickList="",
            snapshot=True,
            regulatorySnapshot=False,
            mktDataOptions=None
        )

        for _ in range(10):
            if math.isnan(market_quote.last):
                self.api_client.sleep(1)
            else:
                return market_quote.last
        print(f'No last price available for {ticker}')
        return 0

    def __handle_order_status(self, trade):
        ''' Callback function for order status updates '''
        print(f'Order [{trade.contract.symbol}] status changed: {trade.orderStatus.status}')
        match trade.orderStatus.status:
            case 'Filled':
                print(f'Order {trade.contract.symbol} has been filled.')
            case _:
                print(f'Other order status: {trade.orderStatus.status}')

    def is_trading_day_open(self, offset_days=0):
        spy_stock = ib_insync.Stock('SPY', 'SMART', self.default_currency)
        self.api_client.qualifyContracts(spy_stock)
        trading_hours = self.api_client.reqContractDetails(spy_stock)[0].liquidHours
        trading_hours_dict = {d.split(':')[0]: d.split(':')[1] for d in trading_hours.split(';')}
        print(trading_hours_dict)

        today_formatted = (datetime.now().astimezone(self.local_timezone) + timedelta(days=offset_days)).strftime('%Y%m%d')

        for k, v in trading_hours_dict.items():
            if (today_formatted in k) and (v == 'CLOSED'):
                return False

        return True

    def is_market_open_now(self):
        spy_stock = ib_insync.Stock('SPY', 'SMART', self.default_currency)
        self.api_client.qualifyContracts(spy_stock)
        trading_hours = self.api_client.reqContractDetails(spy_stock)[0].liquidHours
        trading_hours_list = [d.split('-') for d in trading_hours.split(';')]
        print(trading_hours_list)

        today_formatted = datetime.now().astimezone(self.local_timezone).strftime('%Y%m%d')
        current_time = datetime.now().astimezone(self.local_timezone).strftime('%H%M')

        for d in trading_hours_list:
            if len(d) > 1 and today_formatted in d[0].split()[0]:
                if current_time > d[0].split(':')[1] and current_time < d[1].split(':')[1]:
                    return True

        return False

    def fetch_transaction_history(self):
        pass


# Entry point for the application
if __name__ == '__main__':
    trading_api = BrokerAPI()
    print(datetime.now().strftime('Current date: %Y-%m-%d'))
    with trading_api.establish_connection() as api_instance:
        accounts_info, positions_info, orders_info = api_instance.retrieve_account_info()
        print(ib_insync.util.df(accounts_info))
        print(ib_insync.util.df(positions_info))
        print(ib_insync.util.df(orders_info))
        print("=" * 30)
        market_open = api_instance.is_trading_day_open()
        market_open_now = api_instance.is_market_open_now()
        print(f'Market Open: {market_open}')
        print(f'Market Open Now: {market_open_now}')
        print("=" * 30)
        print(api_instance.fetch_last_price('SSO'))
        if market_open and market_open_now:
            last_price = api_instance.fetch_last_price('AAPL')
            print(f'Last price for AAPL: {last_price}')
            api_instance.submit_order('AAPL', 1)