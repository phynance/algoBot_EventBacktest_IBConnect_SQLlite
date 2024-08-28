import pandas as pd
import datetime
import yfinance as yf


def get_sp500_stocks():
    """
    Get the list of S&P 500 stocks from Wikipedia.
    :return: A list of S&P 500 stock symbols.
    """
    sp500_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    table = pd.read_html(sp500_url)
    sp500_df = table[0]
    return sp500_df['Symbol'].tolist()


class StockDataFetcher:
    def __init__(self, start_date, end_date, symbols=None):
        """
        Initialize the SP500DataFetcher with a start date and an end date.

        :param start_date: The start date for fetching historical data (format: 'YYYY-MM-DD').
        :param end_date: The end date for fetching historical data (format: 'YYYY-MM-DD').
        :param symbols: List of stock symbols to fetch data for. If None, fetches S&P 500 stocks.
        """
        self.start_date = start_date
        self.end_date = end_date
        self.symbols = symbols if symbols else get_sp500_stocks()

    def fetch_data(self):
        """
        Fetch historical adjusted close prices for S&P 500 stocks.

        :return: A DataFrame containing the adjusted close prices of S&P 500 stocks.
        """
        data_dict = {}
        for symbol in self.symbols:
            print(f"Fetching data for {symbol}...")
            try:
                stock_data = yf.download(symbol, start=self.start_date, end=self.end_date)
                data_dict[symbol] = stock_data['Adj Close']
            except Exception as e:
                print(f"Could not fetch data for {symbol}: {e}")
        # Combine all data into a single DataFrame
        closing_prices = pd.concat(data_dict, axis=1)

        return closing_prices

    def save_to_csv(self, df, filename):
        """
        Save the DataFrame to a CSV file.

        :param df: The DataFrame to save.
        :param filename: The name of the CSV file.
        """
        df.to_csv(filename)
        print(f"Data fetching complete. Saved to {filename}.")


# Example usage
if __name__ == "__main__":
    # Set the date range for the last 10 years
    #end_date = datetime.datetime.now()
    end_date = "2012-12-31"
    start_date = "2007-01-01"

    # fetcher = StockDataFetcher(start_date=start_date, end_date=end_date)
    fetcher = StockDataFetcher(start_date=start_date, end_date=end_date, symbols=['SPY'])
    closing_prices = fetcher.fetch_data()
    fetcher.save_to_csv(closing_prices, 'SPY_2007_2012.csv')
    #fetcher.save_to_csv(closing_prices, 'sp500_closing_prices_last_10_years.csv')
