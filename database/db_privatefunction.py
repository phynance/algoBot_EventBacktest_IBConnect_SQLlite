import os
import sqlite3
from contextlib import contextmanager
import pandas as pd


########################################################################
# Sqlite3 private functions
########################################################################

class DatabaseManager:
    def __init__(self):
        self.IB_SQLITE_DB_NAME = 'IB_SQLITE_DB.db'
        self.IB_SQLITE_TRANSACTION_TBL_NAME = 'transactions'
        self.IB_SQLITE_CPPI_TBL_NAME = 'cppi'
        self.IB_SQLITE_ORDER_TBL_NAME = 'orders'

    @contextmanager
    def sqlite_connect(self):
        dirs = os.path.dirname(os.path.abspath(__file__))
        try:
            db_path = os.path.join(dirs, self.IB_SQLITE_DB_NAME)
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

        if tbl_name == self.IB_SQLITE_TRANSACTION_TBL_NAME:
            conn.execute(f'''CREATE TABLE {self.IB_SQLITE_TRANSACTION_TBL_NAME}
                (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                CREATE_TIME DATETIME NOT NULL,
                PORTFOLIO_CLOSE_VALUE FLOAT NOT NULL,
                SPY_CLOSE_PRICE FLOAT NOT NULL,
                COMMISSION FLOAT NOT NULL);
            ''')
        elif tbl_name == self.IB_SQLITE_CPPI_TBL_NAME:
            conn.execute(f'''CREATE TABLE {self.IB_SQLITE_CPPI_TBL_NAME}
                (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                CREATE_TIME DATETIME NOT NULL,
                MAX_ASSET FLOAT NOT NULL,
                E_RATIO FLOAT NOT NULL,
                B_RATIO FLOAT NOT NULL);
            ''')
        elif tbl_name == self.IB_SQLITE_ORDER_TBL_NAME:
            conn.execute(f'''CREATE TABLE {self.IB_SQLITE_ORDER_TBL_NAME}
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

# Example usage
if __name__ == "__main__":
    db_manager = DatabaseManager()

    # Create tables only if they do not exist
    with db_manager.sqlite_connect() as conn:
        if not db_manager.__sqlite_is_table_exist(conn, db_manager.IB_SQLITE_TRANSACTION_TBL_NAME):
            db_manager.__sqlite_create_table(conn, db_manager.IB_SQLITE_TRANSACTION_TBL_NAME)

        if not db_manager.__sqlite_is_table_exist(conn, db_manager.IB_SQLITE_CPPI_TBL_NAME):
            db_manager.__sqlite_create_table(conn, db_manager.IB_SQLITE_CPPI_TBL_NAME)

        if not db_manager.__sqlite_is_table_exist(conn, db_manager.IB_SQLITE_ORDER_TBL_NAME):
            db_manager.__sqlite_create_table(conn, db_manager.IB_SQLITE_ORDER_TBL_NAME)

        # Insert a record
        insert_sql = f"INSERT INTO {db_manager.IB_SQLITE_TRANSACTION_TBL_NAME} (CREATE_TIME, PORTFOLIO_CLOSE_VALUE, SPY_CLOSE_PRICE, COMMISSION) VALUES (?, ?, ?, ?)"
        db_manager.__sqlite_insert_record(conn, insert_sql, ("2024-06-15", 10000.0, 300.0, 10.0), db_manager.IB_SQLITE_TRANSACTION_TBL_NAME)

        # Query data
        df = db_manager.__sqlite_query_data(conn, db_manager.IB_SQLITE_TRANSACTION_TBL_NAME)
        print(df)
