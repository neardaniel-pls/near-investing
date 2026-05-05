import pandas as pd
import numpy as np
from src.optimization import optimize_portfolio
from src.portfolio import build_portfolio_returns
from src.metrics import sharpe_ratio, annualized_return, annualized_volatility, max_drawdown, cagr


def rolling_optimize(
    prices: pd.DataFrame,
    target: str = "max_sharpe",
    train_window: int = 252,
    test_window: int = 21,
    step: int = 21,
    risk_free_rate: float = 0.04,
) -> pd.DataFrame:
    results = []
    all_test_returns = []
    dates = prices.index
    n = len(dates)

    for start_idx in range(0, n - train_window - test_window + 1, step):
        train_end = start_idx + train_window
        test_end = train_end + test_window

        if test_end > n:
            break

        train_prices = prices.iloc[start_idx:train_end]
        test_prices = prices.iloc[train_end:test_end]

        try:
            weights = optimize_portfolio(train_prices, target=target, risk_free_rate=risk_free_rate)
        except Exception:
            weights = {t: 1.0 / len(prices.columns) for t in prices.columns}

        test_rets = build_portfolio_returns(test_prices, weights)
        train_rets = build_portfolio_returns(train_prices, weights)

        perf = {
            "date": dates[train_end],
            "weights": weights,
            "train_sharpe": sharpe_ratio(train_rets, rf=risk_free_rate),
            "train_return": annualized_return(train_rets),
            "train_volatility": annualized_volatility(train_rets),
            "train_max_dd": max_drawdown(train_rets),
            "test_return": (1 + test_rets).prod() - 1,
            "test_volatility": annualized_volatility(test_rets) if len(test_rets) > 1 else 0.0,
        }
        results.append(perf)
        all_test_returns.append(test_rets)

    return pd.DataFrame(results)


def walk_forward_test_returns(rolling_results: pd.DataFrame, prices: pd.DataFrame) -> pd.Series:
    all_rets = []
    for _, row in rolling_results.iterrows():
        weights = row["weights"]
        date = row["date"]
        if date in prices.index:
            idx = prices.index.get_loc(date)
            if idx < len(prices) - 1:
                next_day_ret = prices.iloc[idx + 1] / prices.iloc[idx] - 1
                port_ret = sum(weights.get(t, 0) * next_day_ret.get(t, 0) for t in weights)
                all_rets.append({"date": prices.index[idx + 1], "return": port_ret})

    if not all_rets:
        return pd.Series(dtype=float)
    df = pd.DataFrame(all_rets).set_index("date")["return"]
    df.name = "Walk-Forward"
    return df


def rolling_weights_over_time(rolling_results: pd.DataFrame) -> pd.DataFrame:
    weights_list = []
    for _, row in rolling_results.iterrows():
        entry = {"date": row["date"]}
        entry.update(row["weights"])
        weights_list.append(entry)
    return pd.DataFrame(weights_list).set_index("date")


def compare_rolling_strategies(
    prices: pd.DataFrame,
    targets: list[str] | None = None,
    train_window: int = 252,
    test_window: int = 21,
    step: int = 21,
    risk_free_rate: float = 0.04,
) -> dict[str, pd.DataFrame]:
    if targets is None:
        targets = ["max_sharpe", "min_volatility", "hrp", "min_cvar"]

    results = {}
    for target in targets:
        results[target] = rolling_optimize(
            prices, target=target, train_window=train_window,
            test_window=test_window, step=step, risk_free_rate=risk_free_rate,
        )
    return results
