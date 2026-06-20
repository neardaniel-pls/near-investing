import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def prices() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2020-01-01", periods=504)
    tickers = ["AAA", "BBB", "CCC"]
    mus = np.array([0.0005, 0.0009, -0.0001])
    sigs = np.array([0.010, 0.015, 0.020])
    rets = rng.normal(mus, sigs, (len(dates), len(tickers)))
    p = 100.0 * np.cumprod(1 + rets, axis=0)
    return pd.DataFrame(p, index=dates, columns=tickers)


@pytest.fixture
def returns(prices) -> pd.Series:
    return prices.pct_change().dropna()


@pytest.fixture
def single_returns() -> pd.Series:
    return pd.Series(np.random.default_rng(7).normal(0.0006, 0.012, 504))
