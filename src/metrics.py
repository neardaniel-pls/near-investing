import pandas as pd
import numpy as np
import quantstats as qs


RISK_FREE_RATE = 0.04


def cagr(returns: pd.Series) -> float:
    total = (1 + returns).prod()
    n_days = len(returns)
    if n_days == 0:
        return 0.0
    return total ** (252 / n_days) - 1


def annualized_return(returns: pd.Series) -> float:
    return cagr(returns)


def annualized_volatility(returns: pd.Series) -> float:
    periods_per_year = 252
    return returns.std(ddof=1) * np.sqrt(periods_per_year)


def sharpe_ratio(returns: pd.Series, rf: float = RISK_FREE_RATE) -> float:
    excess = annualized_return(returns) - rf
    vol = annualized_volatility(returns)
    if vol == 0:
        return 0.0
    return excess / vol


def sortino_ratio(returns: pd.Series, rf: float = RISK_FREE_RATE) -> float:
    threshold = rf / 252
    downside_diff = np.minimum(returns - threshold, 0.0)
    downside_dev = np.sqrt((downside_diff ** 2).mean()) * np.sqrt(252)
    excess = annualized_return(returns) - rf
    if downside_dev == 0:
        return float("inf")
    return excess / downside_dev


def calmar_ratio(returns: pd.Series, rf: float = RISK_FREE_RATE) -> float:
    ann_ret = annualized_return(returns)
    mdd = max_drawdown(returns)
    if mdd == 0:
        return 0.0
    return (ann_ret - rf) / abs(mdd)


def max_drawdown(returns: pd.Series) -> float:
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    return drawdown.min()


def cvar(returns: pd.Series, confidence: float = 0.95) -> float:
    var = np.percentile(returns, (1 - confidence) * 100)
    tail = returns[returns <= var]
    if len(tail) == 0:
        return var
    return tail.mean()


def omega_ratio(returns: pd.Series, threshold: float = RISK_FREE_RATE / 252) -> float:
    gains = returns[returns > threshold] - threshold
    losses = threshold - returns[returns < threshold]
    if losses.sum() == 0:
        return float("inf")
    return gains.sum() / losses.sum()


def treynor_ratio(returns: pd.Series, beta: float, rf: float = RISK_FREE_RATE) -> float:
    excess = annualized_return(returns) - rf
    if beta == 0:
        return 0.0
    return excess / beta


def information_ratio(returns: pd.Series, benchmark_returns: pd.Series) -> float:
    aligned_bench = benchmark_returns.reindex(returns.index).dropna()
    aligned_ret = returns.reindex(aligned_bench.index).dropna()
    active = aligned_ret - aligned_bench
    if active.std() == 0:
        return 0.0
    tracking_error = active.std() * np.sqrt(252)
    return active.mean() * 252 / tracking_error


def compute_beta(returns: pd.Series, benchmark_returns: pd.Series) -> float:
    aligned_bench = benchmark_returns.reindex(returns.index).dropna()
    aligned_ret = returns.reindex(aligned_bench.index).dropna()
    covariance = aligned_ret.cov(aligned_bench)
    variance = aligned_bench.var()
    if variance == 0:
        return 0.0
    return covariance / variance


def compute_all_metrics(returns: pd.Series, benchmark_returns: pd.Series | None = None, rf: float = RISK_FREE_RATE) -> dict:
    metrics = {
        "CAGR": cagr(returns),
        "Annualized Return": annualized_return(returns),
        "Annualized Volatility": annualized_volatility(returns),
        "Sharpe Ratio": sharpe_ratio(returns, rf=rf),
        "Sortino Ratio": sortino_ratio(returns, rf=rf),
        "Calmar Ratio": calmar_ratio(returns, rf=rf),
        "Omega Ratio": omega_ratio(returns),
        "Max Drawdown": max_drawdown(returns),
        "CVaR (95%)": cvar(returns),
        "Skewness": returns.skew(),
        "Kurtosis": returns.kurtosis(),
        "Best Day": returns.max(),
        "Worst Day": returns.min(),
        "Avg Daily Return": returns.mean(),
    }
    if benchmark_returns is not None:
        beta = compute_beta(returns, benchmark_returns)
        metrics["Beta"] = beta
        metrics["Treynor Ratio"] = treynor_ratio(returns, beta, rf=rf)
        metrics["Information Ratio"] = information_ratio(returns, benchmark_returns)
        metrics["Alpha"] = annualized_return(returns) - (rf + beta * (annualized_return(benchmark_returns) - rf))
    return metrics


def metrics_table(returns_dict: dict[str, pd.Series], benchmark_returns: pd.Series | None = None, rf: float = RISK_FREE_RATE) -> pd.DataFrame:
    rows = {}
    for name, ret in returns_dict.items():
        rows[name] = compute_all_metrics(ret, benchmark_returns, rf=rf)
    df = pd.DataFrame(rows).T
    df.index.name = "Asset"
    return df


def quantstats_report(returns: pd.Series, benchmark: str = "SPY", title: str = "Strategy") -> None:
    qs.reports.html(returns, benchmark=benchmark, title=title, output=f"{title.replace(' ', '_')}_report.html")
