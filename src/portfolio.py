import pandas as pd
import numpy as np


def build_portfolio_returns(prices: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    returns = prices.pct_change().dropna()
    tickers = list(weights.keys())
    w = np.array([weights[t] for t in tickers])
    portfolio = (returns[tickers] * w).sum(axis=1)
    portfolio.name = "Portfolio"
    return portfolio


def equity_curve(returns: pd.Series, initial_value: float = 10000) -> pd.Series:
    cum = (1 + returns).cumprod()
    return initial_value * cum


def drawdown_series(returns: pd.Series) -> pd.Series:
    cum = (1 + returns).cumprod()
    running_max = cum.cummax()
    return (cum - running_max) / running_max


def rebalanced_portfolio_returns(prices: pd.DataFrame, weights: dict[str, float], rebalance_freq: str = "M") -> pd.Series:
    returns = prices.pct_change().dropna()
    tickers = list(weights.keys())
    w = np.array([weights[t] for t in tickers])
    asset_returns = returns[tickers]
    dates = asset_returns.index
    portfolio = pd.Series(0.0, index=dates, name="Rebalanced Portfolio")
    current_weights = w.copy()
    last_rebalance = dates[0]

    for i, date in enumerate(dates):
        portfolio.iloc[i] = (current_weights * asset_returns.iloc[i].values).sum()
        current_weights = current_weights * (1 + asset_returns.iloc[i].values)
        current_weights = current_weights / current_weights.sum()

        if i > 0:
            if rebalance_freq == "M" and date.month != last_rebalance.month:
                current_weights = w.copy()
                last_rebalance = date
            elif rebalance_freq == "Q" and date.quarter != last_rebalance.quarter:
                current_weights = w.copy()
                last_rebalance = date
            elif rebalance_freq == "Y" and date.year != last_rebalance.year:
                current_weights = w.copy()
                last_rebalance = date

    return portfolio


def compare_portfolios(portfolios: dict[str, pd.Series], initial_value: float = 10000) -> pd.DataFrame:
    curves = {}
    for name, ret in portfolios.items():
        curves[name] = equity_curve(ret, initial_value)
    return pd.DataFrame(curves)
