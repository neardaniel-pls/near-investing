import pandas as pd
import numpy as np
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.optimization import optimize_portfolio
from src.portfolio import build_portfolio_returns
from src.metrics import sharpe_ratio, annualized_return, annualized_volatility, max_drawdown


def rolling_optimize(
    prices: pd.DataFrame,
    target: str = "max_sharpe",
    train_window: int = 252,
    test_window: int = 21,
    step: int = 21,
    risk_free_rate: float = 0.04,
) -> pd.DataFrame:
    results = []
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
            logging.warning("Rolling optimize failed at %s, using equal weights", dates[train_end])
            weights = {t: 1.0 / len(prices.columns) for t in prices.columns}

        test_rets = build_portfolio_returns(test_prices, weights)
        train_rets = build_portfolio_returns(train_prices, weights)

        perf = {
            "date": dates[train_end],
            "weights": weights,
            "test_window": test_window,
            "train_sharpe": sharpe_ratio(train_rets, rf=risk_free_rate),
            "train_return": annualized_return(train_rets),
            "train_volatility": annualized_volatility(train_rets),
            "train_max_dd": max_drawdown(train_rets),
            "test_return": (1 + test_rets).prod() - 1,
            "test_volatility": annualized_volatility(test_rets) if len(test_rets) > 1 else 0.0,
        }
        results.append(perf)

    return pd.DataFrame(results)


def walk_forward_test_returns(rolling_results: pd.DataFrame, prices: pd.DataFrame) -> pd.Series:
    all_rets = []
    for _, row in rolling_results.iterrows():
        weights = row["weights"]
        date = row["date"]
        test_window = row.get("test_window", 21)
        if date in prices.index:
            idx = prices.index.get_loc(date)
            end_idx = min(idx + test_window, len(prices))
            if idx < end_idx:
                window_prices = prices.iloc[idx:end_idx]
                tickers = list(weights.keys())
                w = np.array([weights.get(t, 0) for t in tickers])
                window_rets = window_prices[tickers].pct_change().dropna()
                if len(window_rets) > 0:
                    port_rets = (window_rets * w).sum(axis=1)
                    for d, r in port_rets.items():
                        all_rets.append({"date": d, "return": r})

    if not all_rets:
        return pd.Series(dtype=float)
    df = pd.DataFrame(all_rets).drop_duplicates(subset="date", keep="last").set_index("date")["return"]
    df.name = "Walk-Forward"
    return df.sort_index()


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
    with ThreadPoolExecutor(max_workers=min(len(targets), 4)) as executor:
        futures = {
            executor.submit(
                rolling_optimize, prices, target=target,
                train_window=train_window, test_window=test_window,
                step=step, risk_free_rate=risk_free_rate,
            ): target
            for target in targets
        }
        for future in as_completed(futures):
            target = futures[future]
            results[target] = future.result()
    return results
