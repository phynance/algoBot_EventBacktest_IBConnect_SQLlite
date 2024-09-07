import abc

class AbstractTradeInterface(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def establish_connection(self):
        pass

    @abc.abstractmethod
    def retrieve_account_info(self):
        pass

    @abc.abstractmethod
    def fetch_last_price(self):
        pass

    @abc.abstractmethod
    def submit_order(self):
        pass

    @abc.abstractmethod
    def is_trading_day_open(self):
        pass

    @abc.abstractmethod
    def is_market_open_now(self):
        pass

    @abc.abstractmethod
    def fetch_transaction_history(self):
        pass