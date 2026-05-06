import pandas as pd
import numpy as np


def simulate_portfolio_monte_carlo(
    returns: pd.Series,
    n_simulations: int = 10000,
    n_days: int = 252,
    initial_value: float = 10000,
    random_seed: int | None = None,
) -> np.ndarray:
    if random_seed is not None:
        np.random.seed(random_seed)
    mean_ret = returns.mean()
    std_ret = returns.std()
    simulated = np.random.normal(mean_ret, std_ret, (n_days, n_simulations))
    cumulative = np.cumprod(1 + simulated, axis=0)
    return initial_value * cumulative


def simulate_multivariate_monte_carlo(
    prices: pd.DataFrame,
    weights: dict[str, float],
    n_simulations: int = 10000,
    n_days: int = 252,
    initial_value: float = 10000,
    random_seed: int | None = None,
    use_historical: bool = True,
) -> np.ndarray:
    if random_seed is not None:
        np.random.seed(random_seed)
    returns = prices.pct_change().dropna()
    tickers = list(weights.keys())
    w = np.array([weights[t] for t in tickers])

    if use_historical:
        portfolio_rets = (returns[tickers] * w).sum(axis=1)
        return simulate_portfolio_monte_carlo(
            portfolio_rets, n_simulations, n_days, initial_value
        )

    mean_returns = returns[tickers].mean().values
    cov_matrix = returns[tickers].cov().values
    simulated = np.random.multivariate_normal(mean_returns, cov_matrix, (n_days, n_simulations))
    portfolio_sim = np.tensordot(simulated, w, axes=([2], [0]))
    cumulative = np.cumprod(1 + portfolio_sim, axis=0)
    return initial_value * cumulative


def simulate_historical_bootstrap(
    returns: pd.Series,
    n_simulations: int = 10000,
    n_days: int = 252,
    initial_value: float = 10000,
    random_seed: int | None = None,
) -> np.ndarray:
    if random_seed is not None:
        np.random.seed(random_seed)
    n = len(returns)
    indices = np.random.randint(0, n, (n_days, n_simulations))
    sampled = returns.values[indices]
    cumulative = np.cumprod(1 + sampled, axis=0)
    return initial_value * cumulative


def monte_carlo_statistics(paths: np.ndarray, confidence: float = 0.95) -> dict:
    final_values = paths[-1, :]
    sorted_final = np.sort(final_values)
    n = len(sorted_final)
    var_idx = int((1 - confidence) * n)
    cvar_idx = max(1, var_idx)

    return {
        "Mean Final Value": np.mean(final_values),
        "Median Final Value": np.median(final_values),
        "Std Final Value": np.std(final_values),
        f"VaR ({confidence:.0%})": sorted_final[var_idx],
        f"CVaR ({confidence:.0%})": sorted_final[:cvar_idx].mean(),
        "Best Case (5%)": sorted_final[int(0.95 * n)],
        "Worst Case (5%)": sorted_final[int(0.05 * n)],
        "Probability of Profit": (final_values > paths[0, 0]).mean(),
        "Probability of >50% Gain": (final_values > paths[0, 0] * 1.5).mean(),
        "Probability of >50% Loss": (final_values < paths[0, 0] * 0.5).mean(),
        "Min Final Value": np.min(final_values),
        "Max Final Value": np.max(final_values),
    }


def monte_carlo_return_stats(paths: np.ndarray, initial_value: float = 10000, confidence: float = 0.95) -> dict:
    final_values = paths[-1, :]
    total_returns = final_values / initial_value - 1
    sorted_returns = np.sort(total_returns)
    n = len(sorted_returns)

    max_drawdowns = []
    for i in range(min(paths.shape[1], 1000)):
        cumulative = paths[:, i]
        running_max = np.maximum.accumulate(cumulative)
        dd = (cumulative - running_max) / running_max
        max_drawdowns.append(dd.min())

    var_cutoff = max(1, int((1 - confidence) * n))
    return {
        "Mean Return": np.mean(total_returns),
        "Median Return": np.median(total_returns),
        "Std Return": np.std(total_returns),
        f"VaR ({confidence:.0%})": sorted_returns[var_cutoff],
        f"CVaR ({confidence:.0%})": sorted_returns[:var_cutoff].mean(),
        "Worst Return": np.min(total_returns),
        "Best Return": np.max(total_returns),
        "Avg Max Drawdown": np.mean(max_drawdowns),
        "Worst Max Drawdown": np.min(max_drawdowns),
        "Probability of Loss": (total_returns < 0).mean(),
    }


def simulate_drawdown_cone(
    returns: pd.Series,
    n_simulations: int = 1000,
    n_days: int = 252,
    initial_value: float = 10000,
    quantiles: list[float] | None = None,
    random_seed: int | None = None,
) -> pd.DataFrame:
    if quantiles is None:
        quantiles = [0.05, 0.25, 0.50, 0.75, 0.95]
    if random_seed is not None:
        np.random.seed(random_seed)

    n = len(returns)
    all_paths = np.zeros((n_days, n_simulations))
    for i in range(n_simulations):
        idx = np.random.randint(0, n, n_days)
        sampled = returns.values[idx]
        cumulative = initial_value * np.cumprod(1 + sampled)
        all_paths[:, i] = cumulative

    result = {}
    for q in quantiles:
        result[f"q{int(q*100)}"] = np.percentile(all_paths, q * 100, axis=1)
    result["mean"] = np.mean(all_paths, axis=1)
    return pd.DataFrame(result)
