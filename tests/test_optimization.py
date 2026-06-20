import numpy as np

from src.optimization import (
    optimize_portfolio, optimize_all_strategies, kelly_criterion,
    efficient_frontier_data,
)


def _valid_weights(w, tickers):
    assert isinstance(w, dict)
    assert set(w.keys()) == set(tickers)
    vals = np.array(list(w.values()))
    assert vals.min() >= -1e-9
    assert abs(vals.sum() - 1.0) < 0.05


def test_optimize_max_sharpe(prices):
    w = optimize_portfolio(prices, target="max_sharpe", risk_free_rate=0.02)
    _valid_weights(w, list(prices.columns))


def test_optimize_min_volatility(prices):
    w = optimize_portfolio(prices, target="min_volatility")
    _valid_weights(w, list(prices.columns))


def test_optimize_hrp(prices):
    w = optimize_portfolio(prices, target="hrp")
    _valid_weights(w, list(prices.columns))


def test_optimize_efficient_return_extreme_target_clamped(prices):
    # An infeasibly high target must not raise (it is clamped internally).
    w = optimize_portfolio(prices, target="efficient_return", target_value=10.0)
    _valid_weights(w, list(prices.columns))


def test_optimize_efficient_risk_extreme_target_clamped(prices):
    w = optimize_portfolio(prices, target="efficient_risk", target_value=0.001)
    _valid_weights(w, list(prices.columns))


def test_optimize_all_strategies_keys(prices):
    res = optimize_all_strategies(prices, risk_free_rate=0.02)
    assert "Max Sharpe" in res and "HRP" in res
    for name, w in res.items():
        assert set(w.keys()) == set(prices.columns)


def test_kelly_returns_dict(prices):
    w = kelly_criterion(prices)
    assert isinstance(w, dict)
    if w:
        assert all(v >= 0 for v in w.values())


def test_efficient_frontier_nonempty(prices):
    rets, risks, ms_pt, mv_pt, points = efficient_frontier_data(prices, risk_free_rate=0.02)
    assert len(rets) == len(risks)
    assert len(rets) > 0
    assert np.all(np.isfinite(risks)) and np.all(np.isfinite(rets))
    assert "Max Sharpe" in points
