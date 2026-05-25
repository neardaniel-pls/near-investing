# Changelog

All notable changes to NEAR Investing are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-25

### Added
- Multi-page Streamlit app with 5 analysis pages
- **Dashboard**: KPI cards, normalized performance charts, data explorer, correlation heatmap, asset rankings, raw data viewer
- **Risk Metrics**: 14+ risk/return metrics per asset (Sharpe, Sortino, Calmar, Omega, CVaR, etc.), rolling metrics over configurable windows, benchmark comparison (Alpha, Beta, Treynor, Information Ratio), drawdown visualization, QuantStats HTML report generation
- **Optimization**: 10 portfolio optimization strategies (Max Sharpe, Min Volatility, Max Quadratic Utility, Efficient Return/Risk, Min CVaR, Min Semivariance, Semivariance Utility, Max Return Min Risk, HRP, Kelly Criterion), Black-Litterman model with custom views and confidences, efficient frontier visualization with strategy points, compare-all ranking by any metric
- **Backtest**: Buy-and-hold and periodic rebalancing (monthly/quarterly/yearly), equity curve and drawdown visualization, conservative/balanced/aggressive allocation comparison, yearly returns heatmap
- **Monte Carlo**: Parametric (normal distribution) and historical bootstrap simulations, configurable paths (1k-50k) and time horizon (3mo-5yr), final value distribution, VaR/CVaR statistics, multi-allocation stress comparison
- **Walk-Forward Optimization**: Rolling window optimization with configurable train/test windows, out-of-sample equity curve, weights-over-time visualization, multi-strategy comparison
- Dual UI modes (Beginner and Advanced) with simplified labels and explanations
- Data caching layer with 1-day TTL (parquet files)
- 9 preset portfolios (Balanced Mix, US Tech Giants, European ETFs, etc.)
- CSV export on all data tables
- Configuration persistence via `data/user_config.json`
- Jupyter notebooks for all analysis (6 notebooks)
- Dark theme with custom color palette

### Technical
- `src/data.py` — Yahoo Finance data fetching with parquet caching
- `src/metrics.py` — 14+ financial metric calculations
- `src/optimization.py` — PyPortfolioOpt-based optimization engine
- `src/portfolio.py` — Portfolio construction, equity curves, rebalancing
- `src/monte_carlo.py` — Parametric and bootstrap simulation engines
- `src/rolling.py` — Rolling/walk-forward optimization with parallel execution
- `src/ui.py` — Shared UI components, mode toggle, weight sliders
- `src/charts.py` — Chart theme and helpers
- `src/styles.py` — Global CSS injection and KPI rendering
- `src/export.py` — CSV download and portfolio summary export
