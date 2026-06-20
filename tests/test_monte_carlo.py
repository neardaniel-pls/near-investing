import numpy as np

from src.monte_carlo import (
    simulate_portfolio_monte_carlo, simulate_historical_bootstrap,
    simulate_multivariate_monte_carlo, monte_carlo_statistics,
    monte_carlo_return_stats,
)


def test_simulate_portfolio_mc_shape_and_finite(single_returns):
    paths = simulate_portfolio_monte_carlo(single_returns, n_simulations=200, n_days=63, random_seed=1)
    assert paths.shape == (63, 200)
    assert np.all(np.isfinite(paths))


def test_historical_bootstrap_shape(single_returns):
    paths = simulate_historical_bootstrap(single_returns, n_simulations=150, n_days=40, random_seed=2)
    assert paths.shape == (40, 150)
    assert np.all(np.isfinite(paths))


def test_multivariate_historical_bootstrap_finite(prices):
    w = {"AAA": 0.5, "BBB": 0.3, "CCC": 0.2}
    paths = simulate_multivariate_monte_carlo(
        prices, w, n_simulations=120, n_days=50, random_seed=3, use_historical=True,
    )
    assert paths.shape == (50, 120)
    assert np.all(np.isfinite(paths))


def test_multivariate_parametric_finite(prices):
    w = {"AAA": 0.5, "BBB": 0.3, "CCC": 0.2}
    paths = simulate_multivariate_monte_carlo(
        prices, w, n_simulations=120, n_days=50, random_seed=4, use_historical=False,
    )
    assert paths.shape == (50, 120)
    assert np.all(np.isfinite(paths))


def test_monte_carlo_statistics_keys_and_finite(single_returns):
    paths = simulate_portfolio_monte_carlo(single_returns, n_simulations=500, n_days=126, random_seed=5)
    stats = monte_carlo_statistics(paths)
    assert "Mean Final Value" in stats and "Probability of Profit" in stats
    assert np.isfinite(stats["Mean Final Value"])
    assert 0.0 <= stats["Probability of Profit"] <= 1.0


def test_monte_carlo_return_stats(single_returns):
    paths = simulate_portfolio_monte_carlo(single_returns, n_simulations=300, n_days=63, random_seed=6)
    stats = monte_carlo_return_stats(paths, initial_value=10000)
    assert np.isfinite(stats["Mean Return"])
    assert 0.0 <= stats["Probability of Loss"] <= 1.0
