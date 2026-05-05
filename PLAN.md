# NEAR Investing — Project Plan

## Goal
Build a portfolio analysis tool that fetches asset data (stocks, ETFs, crypto), computes risk/return metrics, supports backtesting and portfolio optimization. Available as both a **Streamlit web app** and **Jupyter notebooks**.

## Tech Stack
- Python 3.13 (venv)
- `yfinance` — data fetching
- `pandas` / `numpy` — data manipulation
- `quantstats` — risk/return metrics (Sharpe, Sortino, Omega, Calmar, etc.)
- `PyPortfolioOpt` — portfolio optimization (mean-variance, efficient frontier, Black-Litterman, CVaR, semivariance)
- `plotly` — interactive visualization
- `streamlit` — web GUI
- Jupyter Notebook — alternative notebook interface

## Phase 1 — MVP (DONE)
1. **Project setup**: Create venv, `requirements.txt`, install dependencies
2. **Data fetching notebook** (`01_data_fetching.ipynb`):
   - Input: list of tickers (e.g., `["AAPL", "VWCE.MI", "BTC-USD"]`)
   - Fetch historical prices via `yfinance`
   - Compute daily returns, correlation matrix, price charts
3. **Risk metrics notebook** (`02_risk_metrics.ipynb`):
   - Individual asset metrics: Sharpe, Sortino, Omega, Calmar, Max Drawdown, Volatility, CVaR, CAGR, Beta, Treynor, Information Ratio, Alpha
   - Rolling metrics charts (rolling Sharpe, rolling volatility)
   - QuantStats HTML report generation
4. **Portfolio backtest notebook** (`03_backtest.ipynb`):
   - Define custom allocation, buy-and-hold vs rebalanced
   - Compare against benchmarks, drawdown charts
   - Yearly returns heatmap, allocation comparison
5. **Portfolio optimization notebook** (`04_optimization.ipynb`):
   - Mean-variance, efficient frontier

## Phase 2 — Advanced Analysis (DONE)
- **Configurable optimization targets**: Choose what to optimize for:
  - `max_sharpe` — Maximize Sharpe ratio
  - `min_volatility` — Minimize portfolio volatility
  - `max_quadratic_utility` — Maximize quadratic utility
  - `efficient_return` — Minimize risk for target return
  - `efficient_risk` — Maximize return for target risk
  - `min_cvar` — Minimize Conditional Value-at-Risk
  - `min_semivariance` — Minimize semivariance (downside risk)
  - `max_sortino` — Maximize Sortino-oriented utility
  - `max_return_min_risk` — Max Sharpe with L2 regularization
  - `hrp` — Hierarchical Risk Parity
- **Black-Litterman model** — incorporate market views and confidences
- **Kelly Criterion** — position sizing based on historical returns
- **Monte Carlo simulation** (`05_monte_carlo.ipynb`):
  - Parametric (normal distribution) and historical bootstrap
  - Final value distribution, VaR, CVaR
  - Drawdown cone, portfolio stress comparison
- **Rolling / Walk-forward optimization** (`06_rolling_optimization.ipynb`):
  - Re-optimize weights over rolling windows
  - Out-of-sample performance tracking
  - Compare multiple strategies over time
- **Data caching layer** — parquet-based cache with TTL, avoids re-fetching

## Phase 3 — Streamlit GUI (DONE)
- Multi-page Streamlit app with 6 pages:
  - **Overview** — fetch data, normalized prices, returns, correlation
  - **Risk Metrics** — full metrics table, risk/return scatter, rolling charts, drawdowns, ratios
  - **Backtest** — portfolio allocation with sliders, buy-and-hold vs rebalanced, allocation comparison
  - **Optimization** — dropdown to select optimization target, Black-Litterman with views, Kelly, efficient frontier
  - **Monte Carlo** — parametric & bootstrap simulations, statistics, portfolio stress comparison
  - **Rolling Optimization** — walk-forward analysis, weights over time, multi-strategy comparison
- Session state shared across pages (fetch once, use everywhere)
- Interactive controls (sliders, dropdowns, number inputs)

## Phase 4 — Future
- Interactive dashboard (Streamlit/Dash)
- Export reports (HTML/PDF summaries)
- Additional data sources (European-specific)
- More advanced risk models (GARCH, copula-based)

## File Structure
```
near-investing/
├── PLAN.md
├── app.py                    # Streamlit entry point
├── requirements.txt
├── pages/
│   ├── 1_Overview.py
│   ├── 2_Risk_Metrics.py
│   ├── 3_Backtest.py
│   ├── 4_Optimization.py
│   ├── 5_Monte_Carlo.py
│   └── 6_Rolling_Optimization.py
├── notebooks/
│   ├── 01_data_fetching.ipynb
│   ├── 02_risk_metrics.ipynb
│   ├── 03_backtest.ipynb
│   ├── 04_optimization.ipynb
│   ├── 05_monte_carlo.ipynb
│   └── 06_rolling_optimization.ipynb
├── src/
│   ├── __init__.py
│   ├── data.py          # data fetching + caching
│   ├── metrics.py       # risk/return metric calculations
│   ├── portfolio.py     # portfolio construction & backtesting
│   ├── optimization.py  # all optimization strategies
│   ├── monte_carlo.py   # Monte Carlo simulations
│   └── rolling.py       # rolling/walk-forward optimization
├── data/
│   └── cache/           # parquet cache files
├── reports/             # generated HTML reports
└── venv/
```

## Quick Start
```bash
source venv/bin/activate

# Streamlit GUI
streamlit run app.py

# Or Jupyter notebooks
jupyter notebook notebooks/
```
