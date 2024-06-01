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
        return \
        df[(datetime.now(self.timezone) - pd.to_datetime(df['CREATE_TIME'], utc=False)) < timedelta(days=time_delta)][
            'COMMISSION'].sum()
