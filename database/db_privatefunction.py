import os
import sqlite3
from contextlib import contextmanager

import pandas as pd


########################################################################
# Sqlite3 private functions
########################################################################


@contextmanager
def sqlite_connect():
    print("testing here")
    dirs = os.path.dirname(os.path.abspath(__file__))
    print(dirs)
    try:
        db_path = os.path.join(dirs, "IB_SQLITE_DB")
        conn = sqlite3.connect(db_path)
        print(f'Sqlite connection established')
        yield conn
        conn.close()
        print(f'Sqlite connection closed')
    except OSError as e:
        print(f'We are having an OS error')


def __sqlite_create_table(self, conn=None, tbl_name=None):
    if not tbl_name or not conn:
        return False

    if tbl_name == "IB_SQLITE_TRANSACTION_TBL_NAME":
        conn.execute(f'''CREATE TABLE {IB_SQLITE_TRANSACTION_TBL_NAME}
            (ID INTEGER PRIMARY KEY AUTOINCREMENT,
            CREATE_TIME DATETIME NOT NULL,
            PORTFOLIO_CLOSE_VALUE FLOAT NOT NULL,
            SPY_CLOSE_PRICE FLOAT NOT NULL,
            COMMISSION FLOAT NOT NULL);
        ''')
    elif tbl_name == IB_SQLITE_CPPI_TBL_NAME:
        conn.execute(f'''CREATE TABLE {IB_SQLITE_CPPI_TBL_NAME}
            (ID INTEGER PRIMARY KEY AUTOINCREMENT,
            CREATE_TIME DATETIME NOT NULL,
            MAX_ASSET FLOAT NOT NULL,
            E_RATIO FLOAT NOT NULL,
            B_RATIO FLOAT NOT NULL);
        ''')
    elif tbl_name == IB_SQLITE_ORDER_TBL_NAME:
        conn.execute(f'''CREATE TABLE {IB_SQLITE_ORDER_TBL_NAME}
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


def __sqlite_is_table_exist(self, conn=None, tbl_name=None):
    if not tbl_name or not conn:
        return False

    c = conn.cursor()

    c.execute(f'''SELECT count(name)
        FROM sqlite_master
        WHERE type="table" AND name="{tbl_name}";
    ''')

    if c.fetchone()[0] == 1:
        # Table exists
        return True
    else:
        # Table does not exist
        return False


def __sqlite_query_data(self, conn=None, tbl_name=None):
    if not conn or not tbl_name:
        return None

    if not self.__sqlite_is_table_exist(conn, tbl_name):
        self.__sqlite_create_table(conn, tbl_name)

    df = pd.read_sql_query(f'SELECT * from {tbl_name};', conn)
    return df


def __sqlite_insert_record(self, conn=None, sql=None, value_tuple: tuple = None, tbl_name=None):
    if not self.__sqlite_is_table_exist(conn, tbl_name):
        self.__sqlite_create_table(conn, tbl_name)

    if not sql:
        raise RuntimeError(f'SQL string is empty')

    conn.execute(sql, value_tuple)
    conn.commit()
    return True


################################################  public functions ####################################################

def get_transactions(self):
    with self.sqlite_connect() as conn:
        df = self.__sqlite_query_data(conn, IB_SQLITE_TRANSACTION_TBL_NAME)
    return df


def get_cppi_variables(self):
    with self.sqlite_connect() as conn:
        df = self.__sqlite_query_data(conn, IB_SQLITE_CPPI_TBL_NAME)
    return df


def update_orders_in_db(self):
    sql = f'''INSERT OR IGNORE INTO {IB_SQLITE_ORDER_TBL_NAME} (CREATE_TIME, SYMBOL, ORDER_ID, ACTION, QUANTITY, ORDER_STATUS, COMMISSION, ACCOUNT) VALUES (?, ?, ?, ?, ?, ?, ?, ?);'''

    with self.sqlite_connect() as conn:
        trades = self.client.trades()
        for trade in trades:
            perm_id = trade.order.permId
            qty = trade.order.filledQuantity
            symbol = trade.contract.symbol
            action = trade.order.action
            commission = sum([fill.commissionReport.commission for fill in trade.fills])
            status = trade.orderStatus.status
            exec_time = trade.log[0].time
            account = trade.order.account
            self.__sqlite_insert_record(
                conn,
                sql,
                (exec_time, symbol, perm_id, action, qty, status, commission, account),
                IB_SQLITE_ORDER_TBL_NAME
            )
    logger.logger.debug(f'Database {IB_SQLITE_ORDER_TBL_NAME} updated')


def update_transactions_in_db(self):
    sql = f'''INSERT OR IGNORE INTO {IB_SQLITE_TRANSACTION_TBL_NAME} (CREATE_TIME, PORTFOLIO_CLOSE_VALUE, SPY_CLOSE_PRICE, COMMISSION) VALUES (?,?,?,?);'''

    # Portfolio value
    portfolio_value = 0
    for account in self.accounts:
        data = self.client.accountValues(account)
        for row in data:
            if row.tag in ['TotalCashBalance', 'StockMarketValue'] and row.currency == self.currency:
                portfolio_value += float(row.value)

    # SPY close value
    benchmark_value = self.get_last_price_from_quote('SPY')

    # Update the latest commission
    commission = self.get_commission_from_db(1)

    with self.sqlite_connect() as conn:
        self.__sqlite_insert_record(
            conn,
            sql,
            (datetime.now(), portfolio_value, benchmark_value, commission),
            IB_SQLITE_TRANSACTION_TBL_NAME
        )
    logger.logger.debug(f'Database {IB_SQLITE_TRANSACTION_TBL_NAME} updated')


def update_cppi_variables_in_db(self, max_asset, E, B):
    sql = f'''INSERT OR IGNORE INTO {IB_SQLITE_CPPI_TBL_NAME} (CREATE_TIME, MAX_ASSET, E_RATIO, B_RATIO) VALUES (?,?,?,?);'''

    with self.sqlite_connect() as conn:
        self.__sqlite_insert_record(
            conn,
            sql,
            (datetime.now(), max_asset, E, B),
            IB_SQLITE_CPPI_TBL_NAME
        )


def get_commission_from_db(self, time_delta: int = 0) -> float:
    with self.sqlite_connect() as conn:
        df = self.__sqlite_query_data(conn, IB_SQLITE_ORDER_TBL_NAME)

    if df.empty:
        return 0
    else:
        return df[(datetime.now(self.timezone) -
