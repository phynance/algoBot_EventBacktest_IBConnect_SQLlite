import os
import sqlite3
from contextlib import contextmanager
import pandas as pd
from datetime import datetime, timedelta
from IBconnect.InteractiveBrokerTradeAPI import InteractiveBrokerTradeAPI
import ib_insync


########################################################################
# Sqlite3 private functions
########################################################################

class DatabaseManager:
    def __init__(self):
        self.IB_SQLITE_DB_NAME = 'IB_SQLITE_DB.db'
        self.IB_SQLITE_TRANSACTION_TBL_NAME = 'transactions'
        self.IB_SQLITE_CPPI_TBL_NAME = 'cppi'
        self.IB_SQLITE_ORDER_TBL_NAME = 'orders'
        self.broker = InteractiveBrokerTradeAPI()
        with self.broker.connect() as ib_conn:
            self.accounts, self.positions, self.orders = ib_conn.get_account_detail()
            self.client = ib_conn.client
        #self.client = self.broker.client
        self.currency = 'USD'
        self.timezone = None  # Replace with actual timezone

    @contextmanager
    def sqlite_connect(self):
        dirs = os.path.dirname(os.path.abspath(__file__))
        try:
            db_path = os.path.join(dirs, self.IB_SQLITE_DB_NAME)
            db_conn = sqlite3.connect(db_path)
            print(f'Sqlite connection established')
            yield db_conn
            db_conn.close()
            print(f'Sqlite connection closed')
        except OSError as e:
            print(f'We are having an OS error')

    def _sqlite_create_table(self, db_conn=None, tbl_name=None):
        if not tbl_name or not db_conn:
            return False

        if tbl_name == self.IB_SQLITE_TRANSACTION_TBL_NAME:
            db_conn.execute(f'''CREATE TABLE {self.IB_SQLITE_TRANSACTION_TBL_NAME}
                (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                CREATE_TIME DATETIME NOT NULL,
                PORTFOLIO_CLOSE_VALUE FLOAT NOT NULL,
                SPY_CLOSE_PRICE FLOAT NOT NULL,
                COMMISSION FLOAT NOT NULL);
            ''')
        elif tbl_name == self.IB_SQLITE_CPPI_TBL_NAME:
            db_conn.execute(f'''CREATE TABLE {self.IB_SQLITE_CPPI_TBL_NAME}
                (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                CREATE_TIME DATETIME NOT NULL,
                MAX_ASSET FLOAT NOT NULL,
                E_RATIO FLOAT NOT NULL,
                B_RATIO FLOAT NOT NULL);
            ''')
        elif tbl_name == self.IB_SQLITE_ORDER_TBL_NAME:
            db_conn.execute(f'''CREATE TABLE {self.IB_SQLITE_ORDER_TBL_NAME}
                (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                CREATE_TIME DATETIME NOT NULL,
                SYMBOL TEXT NOT NULL,
                ORDER_ID TEXT NOT NULL UNIQUE,
                ACTION TEXT NOT NULL,
                QUANTITY INT NOT NULL,
                ORDER_STATUS TEXT NOT NULL,
                COMMISSION FLOAT NOT NULL,
                ACCOUNT TEXT NOT NULL);
            ''')

        return True

    def _sqlite_is_table_exist(self, db_conn=None, tbl_name=None):
        if not tbl_name or not db_conn:
            return False

        db_c = db_conn.cursor()

        db_c.execute(f'''SELECT count(name)
            FROM sqlite_master
            WHERE type="table" AND name="{tbl_name}";
        ''')

        if db_c.fetchone()[0] == 1:
            # Table exists
            return True
        else:
            # Table does not exist
            return False

    def _sqlite_query_data(self, db_conn=None, tbl_name=None):
        if not db_conn or not tbl_name:
            return None

        if not self._sqlite_is_table_exist(db_conn, tbl_name):
            self._sqlite_create_table(db_conn, tbl_name)

        df = pd.read_sql_query(f'SELECT * from {tbl_name};', db_conn)
        return df

    def _sqlite_insert_record(self, db_conn=None, sql=None, value_tuple: tuple = None, tbl_name=None):
        if not self._sqlite_is_table_exist(db_conn, tbl_name):
            self._sqlite_create_table(db_conn, tbl_name)

        if not sql:
            raise RuntimeError(f'SQL string is empty')

        db_conn.execute(sql, value_tuple)
        db_conn.commit()
        return True

    ################################################
    # Public functions
    ################################################

    def get_transactions(self):
        with self.sqlite_connect() as db_conn:
            df = self._sqlite_query_data(db_conn, self.IB_SQLITE_TRANSACTION_TBL_NAME)
        return df

    def get_cppi_variables(self):
        with self.sqlite_connect() as db_conn:
            df = self._sqlite_query_data(db_conn, self.IB_SQLITE_CPPI_TBL_NAME)
        return df

    def update_orders_in_db(self):
        sql = f'''INSERT OR IGNORE INTO {self.IB_SQLITE_ORDER_TBL_NAME} (CREATE_TIME, SYMBOL, ORDER_ID, ACTION, QUANTITY, ORDER_STATUS, COMMISSION, ACCOUNT) VALUES (?, ?, ?, ?, ?, ?, ?, ?);'''

        with self.sqlite_connect() as db_conn:
            trades = self.client.trades()  # Replace with actual trades fetching method
            for trade in trades:
                perm_id = trade.order.permId
                qty = trade.order.filledQuantity
                symbol = trade.contract.symbol
                action = trade.order.action
                commission = sum([fill.commissionReport.commission for fill in trade.fills])
                status = trade.orderStatus.status
                exec_time = trade.log[0].time
                account = trade.order.account
                self._sqlite_insert_record(
                    db_conn,
                    sql,
                    (exec_time, symbol, perm_id, action, qty, status, commission, account),
                    self.IB_SQLITE_ORDER_TBL_NAME
                )
        print(f'Database {self.IB_SQLITE_ORDER_TBL_NAME} updated')

    def update_transactions_in_db(self):
        sql = f'''INSERT OR IGNORE INTO {self.IB_SQLITE_TRANSACTION_TBL_NAME} (CREATE_TIME, PORTFOLIO_CLOSE_VALUE, SPY_CLOSE_PRICE, COMMISSION) VALUES (?,?,?,?);'''

        # Portfolio value
        portfolio_value = 0
        for account in self.accounts:
            data = self.client.accountValues(account)  # Replace with actual account value fetching method
            for row in data:
                if row.tag in ['TotalCashBalance', 'StockMarketValue'] and row.currency == self.currency:
                    portfolio_value += float(row.value)

        # SPY close value
        with self.broker.connect() as ib_conn:
            benchmark_value = ib_conn.get_last_price_from_quote('SPY')  # Replace with actual method to get SPY price

        # Update the latest commission
        commission = self.get_commission_from_db(1)

        with self.sqlite_connect() as db_conn:
            self._sqlite_insert_record(
                db_conn,
                sql,
                (datetime.now(), portfolio_value, benchmark_value, commission),
                self.IB_SQLITE_TRANSACTION_TBL_NAME
            )
        print(f'Database {self.IB_SQLITE_TRANSACTION_TBL_NAME} updated')

    def update_cppi_variables_in_db(self, max_asset, E, B):
        sql = f'''INSERT OR IGNORE INTO {self.IB_SQLITE_CPPI_TBL_NAME} (CREATE_TIME, MAX_ASSET, E_RATIO, B_RATIO) VALUES (?,?,?,?);'''

        with self.sqlite_connect() as db_c:
            self._sqlite_insert_record(
                db_c,
                sql,
                (datetime.now(), max_asset, E, B),
                self.IB_SQLITE_CPPI_TBL_NAME
            )

    def get_commission_from_db(self, time_delta: int = 0) -> float:
        with self.sqlite_connect() as db_c:
            df = self._sqlite_query_data(db_c, self.IB_SQLITE_ORDER_TBL_NAME)

        if df.empty:
            return 0
        else:
            return df[(datetime.now(self.timezone) - pd.to_datetime(df['CREATE_TIME'], utc=False)) < timedelta(
                days=time_delta)]['COMMISSION'].sum()


# Example usage
if __name__ == "__main__":

    db_manager = DatabaseManager()

    # Create tables only if they do not exist
    with db_manager.sqlite_connect() as db_conn:
        if not db_manager._sqlite_is_table_exist(db_conn, db_manager.IB_SQLITE_TRANSACTION_TBL_NAME):
            db_manager._sqlite_create_table(db_conn, db_manager.IB_SQLITE_TRANSACTION_TBL_NAME)

        if not db_manager._sqlite_is_table_exist(db_conn, db_manager.IB_SQLITE_CPPI_TBL_NAME):
            db_manager._sqlite_create_table(db_conn, db_manager.IB_SQLITE_CPPI_TBL_NAME)

        if not db_manager._sqlite_is_table_exist(db_conn, db_manager.IB_SQLITE_ORDER_TBL_NAME):
            db_manager._sqlite_create_table(db_conn, db_manager.IB_SQLITE_ORDER_TBL_NAME)

    # Example usage of public methods
    transactions_df = db_manager.get_transactions()
    print(transactions_df)

    cppi_df = db_manager.get_cppi_variables()
    print(cppi_df)

    db_manager.update_orders_in_db()
    db_manager.update_transactions_in_db()

    # Updating CPPI variables
    db_manager.update_cppi_variables_in_db(max_asset=1000, E=0.5, B=0.5)

    # Fetching commission from DB
    commission = db_manager.get_commission_from_db(time_delta=1)
    print(f"Commission from last day: {commission}")
