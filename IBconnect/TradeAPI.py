import abc

class AbstractTradeInterface(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def connect(self):
        pass

    @abc.abstractmethod
    def get_account_detail(self):
        pass

    @abc.abstractmethod
    def get_last_price_from_quote(self):
        pass

    @abc.abstractmethod
    def place_order(self):
        pass

    @abc.abstractmethod
    def is_market_open(self):
        pass

    @abc.abstractmethod
    def is_market_open_now(self):
        pass

    @abc.abstractmethod
    def get_transactions(self):
        pass