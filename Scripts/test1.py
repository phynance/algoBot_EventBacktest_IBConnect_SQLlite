# InteractiveBrokerTradeAPI.py
from contextlib import contextmanager
import ib_insync
from IBconnect.TradeAPI import AbstractTradeInterface


class InteractiveBrokerTradeAPI(AbstractTradeInterface):
    def __init__(self, currency='USD'):
        self.client = None
        self.accounts = []
        self.currency = currency

    @contextmanager
    def connect(self):
        self.client = ib_insync.IB()  # initialize client
        self.client.connect('127.0.0.1', 7497, 1)

        yield self

        self.client.disconnect()
        self.client.sleep(2)  # make sure the connection is closed before next time you connect to IBKR API service

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
        return acc_data

    def get_last_price_from_quote(self):
        pass

    def place_order(self):
        pass

    def is_market_open(self):
        pass

    def is_market_open_now(self):
        pass

    def get_transactions(self):
        pass


# Main function
if __name__ == '__main__':
    broker = InteractiveBrokerTradeAPI()
    with broker.connect() as c:
        accounts = c.get_account_detail()
        print(accounts)
