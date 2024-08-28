import numpy as np
import pandas as pd


def create_equity_curve_dataframe(data_df):
    data_df['net_wealth'] = data_df['net_wealth'].astype(float)
    data_df['returns'] = data_df['net_wealth'].pct_change().fillna(0)
    data_df['equity_curve'] = (1.0 + data_df['returns']).cumprod()
    return data_df


def calculate_sharpe_ratio(returns, periods=252):
    return (np.sqrt(periods) * np.mean(returns)) / np.std(returns)


def calculate_annualized_return(equity_curve):
    total_periods = len(equity_curve) - 1
    total_return = equity_curve.iloc[-1] / equity_curve.iloc[0] - 1
    annualized_return = (1 + total_return) ** (
                252 / total_periods) - 1  # Assuming daily returns and 252 trading days in a year
    return annualized_return


def calculate_calmar_ratio(equity_curve):
    annualized_return = calculate_annualized_return(equity_curve)
    max_drawdown, _ = calculate_drawdowns(equity_curve)
    calmar_ratio = annualized_return / max_drawdown
    return calmar_ratio


def calculate_drawdowns(equity_curve):
    hwm = [0]
    eq_index = equity_curve.index
    drawdown = pd.Series(index=eq_index)
    duration = pd.Series(index=eq_index)

    for i in range(1, len(eq_index)):
        current_hwm = max(hwm[i - 1], equity_curve.iloc[i])
        hwm.append(current_hwm)
        drawdown.iloc[i] = hwm[i] - equity_curve.iloc[i]
        duration.iloc[i] = 0 if drawdown.iloc[i] == 0 else duration.iloc[i - 1] + 1

    return drawdown.max(), duration.max()
