# Dashboard Guide

The Dashboard is your portfolio's home base — a high-level overview of performance, data exploration, and asset rankings.

## Accessing the Dashboard

1. Fetch data on the home page (or load the sample portfolio)
2. Navigate to **Dashboard** (first page in the workflow)

## KPI Cards

At the top of the page, you'll see key performance indicators for an equal-weight portfolio:

| KPI | Description |
|-----|-------------|
| **Total Return** | Total gain/loss in dollars and percentage on your initial investment |
| **CAGR** | Compound Annual Growth Rate — your average yearly return with compounding |
| **Sharpe Ratio** | Risk-adjusted return. Above 1.0 is good, above 2.0 is excellent |
| **Volatility** | Annualized standard deviation of daily returns — how much prices swing |
| **Max Drawdown** | Largest peak-to-trough decline — the worst drop you would have endured |

These metrics use equal-weight allocation (same % in each asset) as a neutral baseline.

## Tabs

### Performance

All prices are **rebased to 100** so you can compare assets with very different price levels (e.g., BTC at $60k vs an ETF at $50).

- Interactive chart with hover tooltips
- Each line represents one asset
- Look for assets that consistently trend upward with fewer dips

**Tip**: Click legend items to show/hide individual assets.

### Data Explorer

Two side-by-side views of your returns data:

- **Left**: Daily percentage returns over time — look for clusters of volatility
- **Right**: Return distribution histogram — a tall, narrow peak means stable returns; fat tails mean extreme events

Below the chart, **Summary Statistics** shows count, mean, std, min, max, and quartiles for each asset's daily returns.

### Correlation

A heatmap showing how assets move together:

| Value | Meaning |
|-------|---------|
| **+1.0** | Move in perfect lockstep |
| **0.0** | No relationship |
| **-1.0** | Move in opposite directions |

**Diversification tip**: Mix assets with low or negative correlations to reduce overall portfolio risk. If all your assets have correlation > 0.8, you're not diversified.

### Asset Rankings

A sortable table ranking assets by key metrics:

- **Return**: Annualized return
- **Volatility**: Annualized volatility
- **Sharpe**: Risk-adjusted score
- **Max DD**: Worst peak-to-trough decline

Values are color-coded: green for positive, red for negative.

### Raw Data

The actual closing prices downloaded from Yahoo Finance. Useful for verification or export.

## Exporting Data

Each tab with tabular data has a **Download CSV** button. Exported files include:
- `returns_summary.csv` — from Data Explorer
- `prices.csv` — from Raw Data

## Navigation

At the bottom of the page, click **Risk →** to proceed to risk analysis, or use the navigation bar at the top.

## Tips

- Use **Beginner mode** if you're new to investing — labels are simplified
- The Dashboard uses equal weights. To see metrics for a specific allocation, go to **Optimize** or **Backtest**
- Correlation is computed on daily returns, not prices — this is the standard approach

---

[Back to Documentation](../README.md) | [Next: Risk Metrics Guide](risk-metrics-guide.md)
