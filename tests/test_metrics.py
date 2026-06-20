import math

import numpy as np
import pandas as pd

from src.metrics import (
    cagr, sharpe_ratio, sortino_ratio, calmar_ratio, omega_ratio,
    max_drawdown, annualized_volatility, annualized_return,
    compute_all_metrics, metrics_table, cvar,
)


def test_cagr_and_vol_finite(single_returns):
    assert np.isfinite(cagr(single_returns))
    assert annualized_volatility(single_returns) > 0
    assert np.isfinite(annualized_return(single_returns))


def test_max_drawdown_non_positive(single_returns):
    assert max_drawdown(single_returns) <= 0


def test_sharpe_finite(single_returns):
    assert np.isfinite(sharpe_ratio(single_returns, rf=0.02))


def test_sortino_no_downside_returns_nan():
    r = pd.Series([0.001] * 100)
    assert isinstance(sortino_ratio(r, rf=0.0), float) and math.isnan(sortino_ratio(r, rf=0.0))


def test_omega_no_losses_returns_nan():
    r = pd.Series([0.001] * 100)
    assert math.isnan(omega_ratio(r, threshold=0.0))


def test_calmar_no_drawdown_returns_nan():
    r = pd.Series([0.001] * 100)
    assert math.isnan(calmar_ratio(r, rf=0.0))


def test_cvar_in_tail(single_returns):
    v = cvar(single_returns, confidence=0.95)
    assert np.isfinite(v)
    assert v <= single_returns.quantile(0.05)


def test_compute_all_metrics_keys_and_no_inf(returns):
    m = compute_all_metrics(returns["AAA"], benchmark_returns=returns["BBB"], rf=0.02)
    for key, val in m.items():
        assert (not isinstance(val, float)) or np.isfinite(val), f"{key} is not finite: {val}"
    assert "Alpha" in m and "Beta" in m and "Treynor Ratio" in m


def test_metrics_table_shape(returns):
    df = metrics_table({"A": returns["AAA"], "B": returns["BBB"]}, rf=0.02)
    assert df.shape[0] == 2
    assert "Sharpe Ratio" in df.columns
