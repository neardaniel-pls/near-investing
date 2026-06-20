import pandas as pd
import numpy as np
import logging
from pypfopt import (
    EfficientFrontier,
    EfficientCVaR,
    EfficientSemivariance,
    risk_models,
    expected_returns,
    HRPOpt,
    black_litterman,
    objective_functions,
)


OPTIMIZATION_TARGETS = [
    "max_sharpe",
    "min_volatility",
    "max_return_min_risk",
    "min_cvar",
    "min_semivariance",
    "semivariance_utility",
    "max_quadratic_utility",
    "efficient_return",
    "efficient_risk",
]


def compute_expected_returns(prices: pd.DataFrame) -> pd.Series:
    return expected_returns.mean_historical_return(prices)


def compute_covariance(prices: pd.DataFrame) -> pd.DataFrame:
    return risk_models.CovarianceShrinkage(prices).ledoit_wolf()


def optimize_portfolio(
    prices: pd.DataFrame,
    target: str = "max_sharpe",
    target_value: float | None = None,
    market_prior: dict[str, float] | None = None,
    views: dict[str, float] | None = None,
    view_confidences: list[float] | None = None,
    risk_free_rate: float = 0.04,
    market_caps: dict[str, float] | None = None,
    risk_aversion: float = 1,
    delta: float = 2.5,
) -> dict[str, float]:
    mu = compute_expected_returns(prices)
    S = compute_covariance(prices)

    if market_prior is not None or views is not None:
        return _black_litterman_optimize(prices, mu, S, target, risk_free_rate, market_prior, views, view_confidences, market_caps, delta)

    if target == "max_sharpe":
        ef = EfficientFrontier(mu, S)
        ef.max_sharpe(risk_free_rate=risk_free_rate)
        return dict(ef.clean_weights())

    elif target == "min_volatility":
        ef = EfficientFrontier(mu, S)
        ef.min_volatility()
        return dict(ef.clean_weights())

    elif target == "max_quadratic_utility":
        ef = EfficientFrontier(mu, S)
        ef.max_quadratic_utility(risk_aversion=risk_aversion)
        return dict(ef.clean_weights())

    elif target == "efficient_return":
        if target_value is None:
            target_value = float(mu.mean())
        ef_minvol = EfficientFrontier(mu, S)
        ef_minvol.min_volatility()
        floor_ret = ef_minvol.portfolio_performance(verbose=False)[0]
        ceil_ret = float(mu.max())
        target_value = min(max(target_value, floor_ret), ceil_ret)
        ef = EfficientFrontier(mu, S)
        ef.efficient_return(target_value)
        return dict(ef.clean_weights())

    elif target == "efficient_risk":
        if target_value is None:
            target_value = float(np.sqrt(np.diag(S).mean())) * np.sqrt(252)
        ef_minvol = EfficientFrontier(mu, S)
        ef_minvol.min_volatility()
        floor_vol = ef_minvol.portfolio_performance(verbose=False)[1]
        ceil_vol = float(np.sqrt(np.diag(S).max())) * np.sqrt(252)
        target_value = min(max(target_value, floor_vol), ceil_vol)
        ef = EfficientFrontier(mu, S)
        ef.efficient_risk(target_value)
        return dict(ef.clean_weights())

    elif target == "min_cvar":
        returns = prices.pct_change().dropna()
        ec = EfficientCVaR(mu, returns, weight_bounds=(0, 1))
        ec.min_cvar()
        return dict(ec.clean_weights())

    elif target == "min_semivariance":
        returns = prices.pct_change().dropna()
        es = EfficientSemivariance(mu, returns)
        es.min_semivariance()
        return dict(es.clean_weights())

    elif target == "semivariance_utility":
        returns = prices.pct_change().dropna()
        es = EfficientSemivariance(mu, returns)
        es.max_quadratic_utility(risk_aversion=1)
        return dict(es.clean_weights())

    elif target == "max_return_min_risk":
        ef = EfficientFrontier(mu, S)
        ef.add_objective(objective_functions.L2_reg, gamma=1)
        ef.max_sharpe(risk_free_rate=risk_free_rate)
        return dict(ef.clean_weights())

    elif target == "hrp":
        return hierarchical_risk_parity(prices)

    else:
        raise ValueError(f"Unknown target: {target}. Choose from: {OPTIMIZATION_TARGETS + ['hrp']}")


def _black_litterman_optimize(
    prices: pd.DataFrame,
    mu: pd.Series,
    S: pd.DataFrame,
    target: str = "max_sharpe",
    risk_free_rate: float = 0.04,
    market_prior: dict[str, float] | None = None,
    views: dict[str, float] | None = None,
    view_confidences: list[float] | None = None,
    market_caps: dict[str, float] | None = None,
    delta: float = 2.5,
) -> dict[str, float]:
    tickers = list(prices.columns)

    if market_prior is not None:
        prior_weights = np.array([market_prior.get(t, 1.0 / len(tickers)) for t in tickers])
        prior_weights = prior_weights / prior_weights.sum()
    elif market_caps is not None:
        mc = np.array([market_caps.get(t, 1.0) for t in tickers])
        prior_weights = mc / mc.sum()
    else:
        prior_weights = np.ones(len(tickers)) / len(tickers)

    if views is not None:
        view_keys = list(views.keys())
        P = np.zeros((len(view_keys), len(tickers)))
        Q = np.array([views[k] for k in view_keys])
        for i, k in enumerate(view_keys):
            if k in tickers:
                P[i, tickers.index(k)] = 1.0
            else:
                for part in k.split("+"):
                    part = part.strip()
                    if part in tickers:
                        P[i, tickers.index(part)] = 1.0 / len(k.split("+"))

        omega = np.diag(np.ones(len(view_keys)))
        if view_confidences is not None and len(view_confidences) == len(view_keys):
            omega = np.diag(np.array(view_confidences) ** 2)

        bl = black_litterman.BlackLittermanModel(
            S, pi=delta * S @ prior_weights, P=P, Q=Q, omega=omega
        )
        bl_returns = bl.bl_returns()
    else:
        bl_returns = mu

    ef = EfficientFrontier(bl_returns, S)
    if target == "max_sharpe":
        ef.max_sharpe(risk_free_rate=risk_free_rate)
    elif target == "min_volatility":
        ef.min_volatility()
    elif target == "max_quadratic_utility":
        ef.max_quadratic_utility()
    else:
        ef.max_sharpe(risk_free_rate=risk_free_rate)
    return dict(ef.clean_weights())


def black_litterman_optimize(
    prices: pd.DataFrame,
    views: dict[str, float],
    view_confidences: list[float] | None = None,
    market_prior: dict[str, float] | None = None,
    target: str = "max_sharpe",
    risk_free_rate: float = 0.04,
) -> dict[str, float]:
    return optimize_portfolio(
        prices, target=target, risk_free_rate=risk_free_rate,
        market_prior=market_prior, views=views, view_confidences=view_confidences,
    )


def mean_variance_optimize(prices: pd.DataFrame) -> dict[str, float]:
    return optimize_portfolio(prices, target="max_sharpe")


def min_volatility_optimize(prices: pd.DataFrame) -> dict[str, float]:
    return optimize_portfolio(prices, target="min_volatility")


def hierarchical_risk_parity(prices: pd.DataFrame) -> dict[str, float]:
    returns = prices.pct_change().dropna()
    hrp = HRPOpt(returns)
    hrp.optimize()
    return dict(hrp.clean_weights())


def kelly_criterion(prices: pd.DataFrame) -> dict[str, float]:
    returns = prices.pct_change().dropna()
    mean_returns = returns.mean() * 252
    var_returns = returns.var() * 252
    kelly = mean_returns / var_returns
    kelly = kelly.clip(upper=1.0, lower=0.0)
    total = kelly.sum()
    if total > 1:
        kelly = kelly / total
    return {k: round(v, 5) for k, v in kelly.items() if v > 0.001}


def efficient_frontier_data(prices: pd.DataFrame, n_points: int = 100, risk_free_rate: float = 0.04) -> tuple[list[float], list[float], dict, dict, dict[str, dict]]:
    mu = compute_expected_returns(prices)
    S = compute_covariance(prices)

    ef_max_sharpe = EfficientFrontier(mu, S)
    ef_max_sharpe.max_sharpe()
    max_sharpe_perf = ef_max_sharpe.portfolio_performance()

    ef_min_vol = EfficientFrontier(mu, S)
    ef_min_vol.min_volatility()
    min_vol_perf = ef_min_vol.portfolio_performance()

    min_ret = min_vol_perf[0]
    max_ret = float(mu.max()) * 0.9
    if max_ret <= min_ret:
        max_ret = float(mu.max())
    if max_ret <= min_ret:
        max_ret = min_ret + abs(min_ret) * 0.01 + 1e-6
    returns_range = np.linspace(min_ret, max_ret, n_points)

    frontier_returns = []
    frontier_risks = []
    for r in returns_range:
        try:
            ef_temp = EfficientFrontier(mu, S)
            ef_temp.efficient_return(r)
            perf = ef_temp.portfolio_performance()
            frontier_returns.append(perf[0])
            frontier_risks.append(perf[1])
        except Exception:
            logging.warning("Efficient frontier: failed to find portfolio for target return %.4f", r)
            continue

    strategy_points = compute_frontier_strategy_points(prices, risk_free_rate=risk_free_rate)

    return (
        frontier_returns,
        frontier_risks,
        {"return": max_sharpe_perf[0], "risk": max_sharpe_perf[1], "sharpe": max_sharpe_perf[2]},
        {"return": min_vol_perf[0], "risk": min_vol_perf[1], "sharpe": min_vol_perf[2]},
        strategy_points,
    )


def compute_frontier_strategy_points(prices: pd.DataFrame, risk_free_rate: float = 0.04) -> dict[str, dict]:
    from src.metrics import sortino_ratio, calmar_ratio, omega_ratio, cvar, max_drawdown
    from src.portfolio import build_portfolio_returns

    mu = compute_expected_returns(prices)
    S = compute_covariance(prices)
    mu_arr = mu.values
    S_arr = S.values
    tickers = list(prices.columns)

    strategies = {
        "Max Sharpe": "max_sharpe",
        "Min Volatility": "min_volatility",
        "Min CVaR": "min_cvar",
        "Min Semivariance": "min_semivariance",
        "Semivariance Utility": "semivariance_utility",
        "Max Quadratic Utility": "max_quadratic_utility",
        "HRP": "hrp",
    }

    def _mv_perf(weights: dict) -> tuple[float, float, float]:
        w = np.array([weights.get(t, 0.0) for t in tickers])
        ret = float(mu_arr @ w)
        risk = float(np.sqrt(w @ S_arr @ w))
        sharpe = (ret - risk_free_rate) / risk if risk > 0 else 0.0
        return ret, risk, sharpe

    points = {}
    for name, target in strategies.items():
        try:
            weights = optimize_portfolio(prices, target=target, risk_free_rate=risk_free_rate)
            port_ret = build_portfolio_returns(prices, weights)
            mv_ret, mv_risk, mv_sharpe = _mv_perf(weights)
            points[name] = {
                "return": mv_ret,
                "risk": mv_risk,
                "sharpe": mv_sharpe,
                "sortino": sortino_ratio(port_ret, rf=risk_free_rate),
                "calmar": calmar_ratio(port_ret, rf=risk_free_rate),
                "omega": omega_ratio(port_ret),
                "max_drawdown": max_drawdown(port_ret),
                "cvar": cvar(port_ret),
                "weights": weights,
            }
        except Exception:
            logging.warning("Failed to compute frontier strategy point: %s", name)

    try:
        kelly_w = kelly_criterion(prices)
        if kelly_w:
            port_ret = build_portfolio_returns(prices, kelly_w)
            mv_ret, mv_risk, mv_sharpe = _mv_perf(kelly_w)
            points["Kelly Criterion"] = {
                "return": mv_ret,
                "risk": mv_risk,
                "sharpe": mv_sharpe,
                "sortino": sortino_ratio(port_ret, rf=risk_free_rate),
                "calmar": calmar_ratio(port_ret, rf=risk_free_rate),
                "omega": omega_ratio(port_ret),
                "max_drawdown": max_drawdown(port_ret),
                "cvar": cvar(port_ret),
                "weights": kelly_w,
            }
    except Exception:
        logging.warning("Failed to compute Kelly Criterion for frontier")

    return points


def optimize_all_strategies(prices: pd.DataFrame, risk_free_rate: float = 0.04, risk_aversion: float = 1) -> dict[str, dict[str, float]]:
    results = {}
    strategies = [
        ("Max Sharpe", "max_sharpe"),
        ("Min Volatility", "min_volatility"),
        ("Max Quadratic Utility", "max_quadratic_utility"),
        ("Min CVaR", "min_cvar"),
        ("Min Semivariance", "min_semivariance"),
        ("Semivariance Utility", "semivariance_utility"),
        ("Max Return Min Risk", "max_return_min_risk"),
        ("HRP", "hrp"),
        ("Kelly Criterion", None),
    ]

    for name, target in strategies:
        try:
            if name == "Kelly Criterion":
                results[name] = kelly_criterion(prices)
            else:
                results[name] = optimize_portfolio(prices, target=target, risk_free_rate=risk_free_rate, risk_aversion=risk_aversion)
        except Exception:
            logging.warning("Failed to optimize strategy: %s", name)
            results[name] = {t: 0.0 for t in prices.columns}

    return results
