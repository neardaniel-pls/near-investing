# Frequently Asked Questions

## General Questions

### Q: What data source does NEAR Investing use?
**A:** All market data is fetched from [Yahoo Finance](https://finance.yahoo.com) via the `yfinance` library. This covers stocks, ETFs, indices, and cryptocurrencies worldwide.

### Q: Does it work with European ETFs?
**A:** Yes. Use the exchange-specific ticker suffix (e.g., `VWCE.MI` for Xetra/Milan, `IWDA.AS` for Euronext Amsterdam, `EUNL.DE` for Xetra). Look up exact symbols at [finance.yahoo.com/lookup](https://finance.yahoo.com/lookup).

### Q: Is this financial advice?
**A:** No. NEAR Investing is a tool for personal analysis and education. All optimization and backtesting results are based on historical data and do not guarantee future performance. Always do your own research.

### Q: Can I use this without installing anything?
**A:** No, it runs as a local Streamlit web app. You need Python and the dependencies installed.

## Data & Caching

### Q: How long does data fetching take?
**A:** Depends on the number of tickers and date range. Typically 5-30 seconds. Data is cached locally for 1 day (parquet files in `data/cache/`).

### Q: Can I change the cache duration?
**A:** The cache TTL is 1 day by default. You can clear the cache from the sidebar: expand "Actions" and click "Clear Cache".

### Q: Why do some tickers show less data than my date range?
**A:** The app warns you when a ticker's data starts later than your requested start date. Adjust the start date to match the earliest available data for all your tickers.

### Q: What currencies are supported?
**A:** All currencies available on Yahoo Finance. Note that the app doesn't convert between currencies — if you mix USD and EUR tickers, returns are computed in each currency separately.

## Metrics & Analysis

### Q: What is the risk-free rate?
**A:** It's the return on a theoretically risk-free investment (e.g., government bonds). Default is 4%. Used in Sharpe, Sortino, Treynor, and Calmar ratios. Adjust it in the sidebar under "Parameters".

### Q: What's a good Sharpe ratio?
**A:** Generally:
- **< 0.5**: Poor risk-adjusted return
- **0.5 - 1.0**: Acceptable
- **1.0 - 2.0**: Good
- **> 2.0**: Excellent

### Q: What's the difference between CAGR and Total Return?
**A:** CAGR (Compound Annual Growth Rate) is the annualized return assuming compounding. Total Return is the simple cumulative gain/loss over the entire period.

### Q: What is CVaR?
**A:** Conditional Value-at-Risk (CVaR), also known as Expected Shortfall, measures the average loss in the worst X% of days (default 5%). It's more sensitive to extreme events than standard volatility.

### Q: How do I interpret the efficient frontier?
**A:** The efficient frontier shows the best possible return for each level of risk. Points on or near the curve are optimal. Points below the curve are suboptimal — you could get the same return with less risk, or more return with the same risk.

## Optimization

### Q: Which optimization strategy should I use?
**A:** Depends on your goal:
- **Max Sharpe** — Best overall risk-adjusted return (most common choice)
- **Min Volatility** — Smoothest ride, lowest price swings
- **Min CVaR** — Protects against extreme losses/crashes
- **HRP** — Robust diversification without relying on return estimates
- **Kelly Criterion** — Maximum long-term growth (can be aggressive)

### Q: What is Black-Litterman?
**A:** A model that starts from market equilibrium and lets you overlay your personal return expectations. For each asset, you set your expected return and confidence level. The optimizer blends your views with market data to produce a more stable allocation.

### Q: Why does the optimizer concentrate in one asset?
**A:** This happens when one asset has significantly better historical metrics. Use **Max Return Min Risk** (regularized Sharpe) for more diversification, or try **HRP** which naturally diversifies.

## Backtesting

### Q: What's the difference between Buy & Hold and Rebalancing?
**A:**
- **Buy & Hold**: Invest once and never touch it. Winners grow beyond their target weight.
- **Rebalancing**: Periodically reset to your target weights (sell winners, buy losers). Enforces discipline and can improve risk-adjusted returns.

### Q: Does backtesting guarantee future results?
**A:** No. Past performance does not guarantee future results. Backtests can overfit to historical data. Use walk-forward optimization (Simulate page) for a more realistic test.

## Simulation

### Q: What's the difference between Historical Bootstrap and Parametric?
**A:**
- **Historical Bootstrap**: Randomly samples from actual past returns. Captures real-world patterns including crashes and fat tails. Recommended for realism.
- **Parametric**: Assumes returns follow a normal distribution. Quick but underestimates extreme events.

### Q: What is walk-forward optimization?
**A:** It tests your strategy as if you were using it in real-time: optimize on a past window, test on the next period, roll forward, and repeat. This is more realistic than a single backtest because it uses only past data for each optimization.

## Troubleshooting

### Q: Getting "No data fetched" error?
**A:**
- Check that your ticker symbols are correct (use [finance.yahoo.com/lookup](https://finance.yahoo.com/lookup))
- Make sure the date range is valid (end date should be before today)
- Some tickers may be delisted or have insufficient history

### Q: "ModuleNotFoundError" when running?
**A:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Q: Streamlit page not loading?
**A:** Make sure you're running from the project root:
```bash
streamlit run app.py
```
Not from inside `pages/` or `src/`.

### Q: Yahoo Finance returning empty data?
**A:** Yahoo Finance occasionally rate-limits requests. Wait a few minutes and try again. The cache helps avoid repeated requests.

## Still Have Questions?

- Check [full documentation](README.md)
- Search [existing issues](https://github.com/neardaniel-pls/near-investing/issues)
- [Open a new issue](https://github.com/neardaniel-pls/near-investing/issues/new)

---

**Last Updated**: 2026-05-25
