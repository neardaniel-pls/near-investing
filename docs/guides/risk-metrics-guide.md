# Risk Metrics Guide

The Risk page provides a deep dive into risk and return characteristics for each asset in your portfolio — 14+ metrics, rolling charts, drawdowns, and benchmark comparison.

## Accessing the Risk Page

1. Fetch data on the home page
2. Navigate to **Risk** (second page in the workflow)

## Benchmark Selection

In the sidebar, you can select a **benchmark** from your tickers (e.g., `^GSPC` for S&P 500). When a benchmark is selected, additional relative metrics are computed:

- **Alpha** — Return above what the CAPM model predicts
- **Beta** — Sensitivity to benchmark movements (>1 = more volatile than benchmark)
- **Treynor Ratio** — Excess return per unit of systematic risk
- **Information Ratio** — Excess return vs benchmark per unit of tracking error

## Full Metrics Table

The main table shows all computed metrics for each asset:

| Metric | What It Measures | Good Value |
|--------|-----------------|------------|
| **CAGR** | Compound Annual Growth Rate | Higher is better |
| **Annualized Volatility** | How much returns swing (annualized std dev) | Lower is better |
| **Sharpe Ratio** | Return per unit of total risk | >1.0 good, >2.0 excellent |
| **Sortino Ratio** | Return per unit of downside risk | >1.0 good |
| **Calmar Ratio** | Return vs. worst drawdown | Higher is better |
| **Omega Ratio** | Probability-weighted gains vs losses | >1.0 good |
| **Max Drawdown** | Worst peak-to-trough decline | Closer to 0% is better |
| **CVaR (95%)** | Average loss in worst 5% of days | Closer to 0 is better |
| **Skewness** | Asymmetry of returns | Positive = more big gains |
| **Kurtosis** | Fat tails (extreme events) | High = more extreme events |
| **Best Day** | Single best daily return | — |
| **Worst Day** | Single worst daily return | — |
| **Avg Daily Return** | Mean of daily returns | Higher is better |

When a benchmark is selected, additional columns appear:

| Metric | What It Measures |
|--------|-----------------|
| **Beta** | How much the asset moves with the benchmark |
| **Treynor Ratio** | Excess return per unit of Beta |
| **Information Ratio** | Active return per unit of tracking error |
| **Alpha** | Return above CAPM prediction |

Expand the **"What do these metrics mean?"** section for inline explanations.

## Risk vs Return Scatter

A scatter plot with annualized volatility on the X-axis and annualized return on the Y-axis.

- Each dot is one asset
- The benchmark (if selected) appears as a star
- **Top-left** is the ideal: high return with low risk
- **Bottom-right** is the worst: low return with high risk

## Risk-Adjusted Ratios

A grouped bar chart comparing Sharpe, Sortino, Calmar, and Omega ratios across all assets. Taller bars = better risk-adjusted performance.

## Rolling Metrics

Expand the **Rolling Metrics** section to see how any metric changes over time.

### Configuration
- **Rolling window**: Number of trading days per calculation window
  - 63 days ≈ 3 months
  - 126 days ≈ 6 months
  - 252 days ≈ 1 year (default)
  - 504 days ≈ 2 years
- **Rolling metric**: Choose from Sharpe, Sortino, Calmar, Omega, Volatility, Max Drawdown, CVaR, CAGR, Skewness, Kurtosis

### How to Read
- **Stable lines**: Risk/return characteristics are consistent over time
- **Wild swings**: The asset's risk profile varies significantly across market regimes
- **Declining Sharpe**: Risk-adjusted performance is deteriorating
- **Spiking volatility**: Periods of market stress

## Drawdowns

Expand the **Drawdowns** section to see how far below its peak each asset has fallen.

- Deeper drawdowns = more pain to hold through
- Longer drawdowns = longer recovery time
- Look for assets with shallow, short drawdowns for more stable holdings

## QuantStats Report

Expand the **Generate QuantStats Report** section to create a detailed HTML report for a single asset using the [QuantStats](https://github.com/ranaroussi/quantstats) library.

1. Select an asset from the dropdown
2. Optionally change the benchmark ticker (default: `SPY`)
3. Click **Generate Report**
4. Download the HTML file

The report includes: cumulative returns, drawdowns, monthly/annual returns, rolling statistics, and much more.

## Exporting Data

Click **Download CSV** below the metrics table to export all metrics as `risk_metrics.csv`.

## Tips

- Compare metrics across assets rather than looking at absolute values
- Use Sortino instead of Sharpe for assets with asymmetric returns (e.g., crypto)
- Rolling metrics reveal whether a good average Sharpe is consistent or driven by one period
- Always consider Max Drawdown alongside returns — a 50% drawdown requires a 100% gain to recover

---

[Back to Documentation](../README.md) | [Previous: Dashboard Guide](dashboard-guide.md) | [Next: Optimization Guide](optimization-guide.md)
