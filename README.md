# NEAR Investing

A personal portfolio analysis and optimization tool built with Streamlit. Fetch real market data from Yahoo Finance, analyze risk, backtest strategies, optimize allocations, and simulate future scenarios — all from a single web UI.

Designed for European investors (UCITS ETFs, European-listed assets).

## Features

**Dashboard** — Overview of your portfolio with KPI cards (return, CAGR, Sharpe, volatility, max drawdown), normalized performance charts, and asset rankings with full names.

**Risk Metrics** — 14+ risk/return metrics per asset (Sharpe, Sortino, Calmar, Omega, CVaR, max drawdown, skewness, kurtosis, etc.). Rolling metrics over configurable windows. Benchmark comparison with Alpha, Beta, Treynor, and Information Ratio.

**Backtest** — Simulate any allocation with buy & hold or periodic rebalancing. Compare conservative/balanced/aggressive presets side by side. Yearly returns heatmap.

**Optimization** — 10 portfolio optimization strategies:
- Mean-Variance: Max Sharpe, Min Volatility, Efficient Return/Risk, Regularized Sharpe
- Downside Risk: Min CVaR, Min Semivariance, Semivariance Utility
- Alternative: HRP (Hierarchical Risk Parity), Kelly Criterion, Black-Litterman
- Efficient Frontier visualization with all strategy points
- "Compare All" ranks strategies by any metric you choose

**Monte Carlo** — Parametric and historical bootstrap simulations with configurable paths and time horizon. Stress-test multiple allocations against thousands of scenarios.

**Rolling Optimization** — Walk-forward analysis with configurable train/test windows. Compare multiple strategies out-of-sample. Weights-over-time visualization.

## Quick Start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## How to Use

1. **Configure** — Pick a preset or enter tickers (one per line) in the sidebar. Set date range, risk-free rate, and initial investment.
2. **Fetch** — Click "Fetch Data" to download prices from Yahoo Finance (cached for 1 day).
3. **Explore** — Navigate through the workflow: Overview → Risk → Backtest → Optimize → Monte Carlo → Rolling.

Look up tickers at [finance.yahoo.com/lookup](https://finance.yahoo.com/lookup).

## Project Structure

```
app.py                      # Main entry point / dashboard
pages/
  1_Overview.py             # Price charts, returns, correlation
  2_Risk_Metrics.py         # Full risk analysis
  3_Backtest.py             # Portfolio backtesting
  4_Optimization.py         # Portfolio optimization
  5_Monte_Carlo.py          # Monte Carlo simulation
  6_Rolling_Optimization.py # Walk-forward analysis
src/
  config.py                 # Default portfolio persistence
  data.py                   # Yahoo Finance data fetching with caching
  metrics.py                # Risk/return metric calculations
  monte_carlo.py            # Monte Carlo simulation engines
  optimization.py           # Portfolio optimization (PyPortfolioOpt)
  portfolio.py              # Portfolio construction & equity curves
  rolling.py                # Rolling/walk-forward optimization
  ui.py                     # Shared UI components
.streamlit/
  config.toml               # Dark theme config
data/
  cache/                    # Cached price data (parquet)
  user_config.json          # Saved default settings
```

## Key Dependencies

- [Streamlit](https://streamlit.io) — web UI
- [yfinance](https://github.com/ranaroussi/yfinance) — market data
- [PyPortfolioOpt](https://github.com/robertmartin8/PyPortfolioOpt) — portfolio optimization
- [Plotly](https://plotly.com/python/) — interactive charts
- [QuantStats](https://github.com/ranaroussi/quantstats) — financial metrics
- [scikit-learn](https://scikit-learn.org) — HRP clustering

## Presets

| Preset | Description |
|--------|-------------|
| Balanced Mix | Stocks + ETFs + crypto |
| US Tech Giants | AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA |
| Dividend & Value | High-dividend European ETFs + value stocks |
| European ETFs | UCITS ETFs listed on EU exchanges (EUR) |
| All-World ETFs | Global diversification via EU-listed ETFs |
| Crypto | BTC, ETH, SOL, ADA, AVAX |
| 60/40 Classic | Stocks / bonds split |
| Golden Butterfly | Stocks + bonds + gold + cash |

## License

Personal use.
