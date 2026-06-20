import numpy as np

from src.portfolio import (
    build_portfolio_returns, equity_curve, drawdown_series,
    rebalanced_portfolio_returns, compare_portfolios,
)


def test_build_portfolio_returns(prices):
    w = {"AAA": 0.5, "BBB": 0.3, "CCC": 0.2}
    port = build_portfolio_returns(prices, w)
    assert port.name == "Portfolio"
    assert len(port) == len(prices) - 1
    assert np.all(np.isfinite(port.values))


def test_equity_curve_starts_near_initial(prices):
    w = {"AAA": 0.5, "BBB": 0.5, "CCC": 0.0}
    port = build_portfolio_returns(prices, w)
    eq = equity_curve(port, initial_value=10000)
    expected_first = 10000 * (1 + port.iloc[0])
    assert abs(eq.iloc[0] - expected_first) < 1e-6
    assert np.all(np.isfinite(eq.values))


def test_drawdown_non_positive(prices):
    port = build_portfolio_returns(prices, {"AAA": 1.0, "BBB": 0.0, "CCC": 0.0})
    dd = drawdown_series(port)
    assert (dd <= 1e-9).all()


def test_rebalanced_returns_length_and_finite(prices):
    w = {"AAA": 0.4, "BBB": 0.4, "CCC": 0.2}
    rb = rebalanced_portfolio_returns(prices, w, rebalance_freq="Q")
    assert len(rb) == len(prices) - 1
    assert np.all(np.isfinite(rb.values))


def test_compare_portfolios_columns(prices):
    w = {"AAA": 0.5, "BBB": 0.5, "CCC": 0.0}
    port = build_portfolio_returns(prices, w)
    curves = compare_portfolios({"P": port}, initial_value=5000)
    assert list(curves.columns) == ["P"]
    assert abs(curves["P"].iloc[0] - 5000 * (1 + port.iloc[0])) < 1e-6
