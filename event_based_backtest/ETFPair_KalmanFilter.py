import yfinance as yf
import pandas as pd
import numpy as np
from pykalman import KalmanFilter
import matplotlib.pyplot as plt


# Function to fetch historical data
def fetch_data(tickers, start_date, end_date):
    data = yf.download(tickers, start=start_date, end=end_date)['Adj Close']
    return data


# Function to implement Kalman filter for pair trading
def kalman_filter_pairs(spy, ivv):
    delta = 1e-5
    trans_cov = delta / (1 - delta) * np.eye(2)
    obs_mat = np.vstack([spy, np.ones(spy.shape)]).T[:, np.newaxis]

    kf = KalmanFilter(n_dim_obs=1, n_dim_state=2,
                      initial_state_mean=np.zeros(2),
                      initial_state_covariance=np.ones((2, 2)),
                      transition_matrices=np.eye(2),
                      observation_matrices=obs_mat,
                      transition_covariance=trans_cov,
                      observation_covariance=1.0)

    state_means, state_covs = kf.filter(ivv.values)
    return state_means


# Fetch historical data
tickers = ['SPY', 'IVV']
start_date = '2020-01-01'
end_date = '2023-01-01'
data = fetch_data(tickers, start_date, end_date)

# Apply Kalman filter
state_means = kalman_filter_pairs(data['SPY'], data['IVV'])
hedge_ratio = -state_means[:, 0]

# Calculate the spread
spread = data['IVV'] + hedge_ratio * data['SPY']

# Plot the spread
plt.figure(figsize=(12, 6))
plt.plot(spread, label='Spread')
plt.axhline(spread.mean(), color='red', linestyle='--', label='Mean')
plt.legend()
plt.title('Spread of IVV and Hedged SPY using Kalman Filter')
plt.show()

# Generate trading signals
z_score = (spread - spread.mean()) / spread.std()
entry_threshold = 2
exit_threshold = 0

data['Positions'] = np.where(z_score > entry_threshold, -1, np.nan)
data['Positions'] = np.where(z_score < -entry_threshold, 1, data['Positions'])
data['Positions'] = np.where(np.abs(z_score) < exit_threshold, 0, data['Positions'])
data['Positions'] = data['Positions'].ffill()

# Calculate strategy returns
data['Market_Returns'] = data['SPY'].pct_change()
data['Strategy_Returns'] = data['Positions'].shift(1) * data['Market_Returns']

# Plot the strategy performance
plt.figure(figsize=(12, 6))
(data['Strategy_Returns'] + 1).cumprod().plot(label='Strategy Returns')
(data['Market_Returns'] + 1).cumprod().plot(label='Market Returns')
plt.legend()
plt.title('Strategy Returns vs Market Returns')
plt.show()
