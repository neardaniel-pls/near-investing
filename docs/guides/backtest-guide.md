# Backtest Guide

The Backtest page simulates how your chosen allocation would have performed historically — with buy-and-hold or periodic rebalancing strategies.

## Accessing the Backtest Page

1. Fetch data on the home page
2. Navigate to **Backtest** (fourth page in the workflow)

## Overview

Backtesting applies your allocation weights to historical price data and shows:
- How your initial investment would have grown (equity curve)
- How far below the peak your portfolio fell (drawdown)
- Risk/return metrics for the simulated period

## Setting Allocation Weights

In the sidebar:

1. **Set weights** using sliders for each asset (0-100%)
2. **Auto-normalize** is enabled by default — weights are rescaled to sum to 100%
3. **Equal Weight**: Reset all to equal percentages
4. **Use Optimized**: Load weights from the last optimization (if available)

### Optimized Weights

If you ran optimization on the Optimize page, the weights are automatically loaded here. A green badge shows which strategy was used.

## Rebalancing

Choose how often to reset your portfolio to the target weights:

| Frequency | Code | Description |
|-----------|------|-------------|
| **None (Buy & Hold)** | — | Invest once, never touch it |
| **Monthly** | `M` | Rebalance every month |
| **Quarterly** | `Q` | Rebalance every quarter |
| **Yearly** | `Y` | Rebalance every year |

### Buy & Hold vs Rebalancing

- **Buy & Hold**: Winners grow beyond their target weight. Simpler, lower transaction costs.
- **Rebalancing**: Periodically sell winners and buy losers to restore target weights. Enforces discipline and can improve risk-adjusted returns through "buy low, sell high."

## Equity Curve & Drawdown

The main chart has two panels:

### Top Panel: Equity Curve
- Portfolio value over time starting from your initial investment
- Shows Buy & Hold (and Rebalanced if selected) curves
- If a benchmark index is in your tickers (e.g., `^GSPC`), it's plotted for comparison

### Bottom Panel: Drawdown
- How far below the peak at each point in time
- Deeper/longer drawdowns = harder to hold through
- Dotted lines show drawdown for each variant

## Metrics Comparison

A side-by-side table comparing risk/return metrics for each portfolio variant:
- Buy & Hold
- Rebalanced (if selected)
- Benchmark (if available)

### Compare Multiple Allocations

Enable **"Compare multiple allocations"** to define up to 3 custom allocations:
- **Conservative**: Your conservative allocation (lower-risk assets)
- **Balanced**: Based on your current weights
- **Aggressive**: Higher allocation to riskier assets (e.g., crypto)

The comparison table shows all variants side by side.

### Equity Curve Comparison

Expand to see all allocations plotted together — quickly spot which strategy grew the most.

### Yearly Returns Heatmap

A color-coded heatmap of annual returns:
- **Green**: Profitable year
- **Red**: Losing year
- Cell values show the percentage return

## Tips

- **Longer date ranges** give more robust backtest results
- **Rebalancing frequency** matters more for volatile portfolios
- **Past performance does not guarantee future results** — backtests can overfit to historical data
- Use the **Simulate page** for Monte Carlo stress-testing and walk-forward validation
- Compare Buy & Hold vs Rebalanced to see if rebalancing adds value for your allocation
- The yearly returns heatmap reveals which years drove most of the performance

---

[Back to Documentation](../README.md) | [Previous: Optimization Guide](optimization-guide.md) | [Next: Simulation Guide](simulation-guide.md)
