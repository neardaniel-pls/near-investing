# Optimization Guide

The Optimize page finds the best asset allocation for your portfolio using 10+ optimization strategies, the efficient frontier, Black-Litterman views, and Kelly Criterion position sizing.

## Accessing the Optimize Page

1. Fetch data on the home page
2. Navigate to **Optimize** (third page in the workflow)

## Overview

The page has three tabs:

1. **All Strategies** — Compare all optimization strategies, ranked by any metric
2. **Single Strategy** — Run one specific optimization with custom parameters
3. **Custom Views & Sizing** — Black-Litterman model and Kelly Criterion

## Tab 1: All Strategies (Compare All)

This is the default view. It runs all strategies at once and ranks them.

### Controls

- **Risk aversion slider** (1-20): Controls how much the optimizer avoids risk in quadratic utility strategies
  - **1-2** (Aggressive): Concentrates in highest-return assets
  - **3-5** (Moderate): Balanced diversification (default: 5)
  - **6-10** (Conservative): More spread across assets
  - **10-20** (Very Conservative): Approaches equal-weight
- **Rank strategies by**: Choose which metric to rank by (Sharpe, Sortino, Calmar, CAGR, etc.)
- **Re-run All**: Force recomputation

### Strategy Ranking

A horizontal bar chart shows all strategies ranked by your chosen metric. The best strategy is highlighted in green.

**The best strategy's weights are automatically saved** for use in the Backtest and Simulate pages.

### Available Strategies

#### Mean-Variance Methods (Markowitz)
| Strategy | Description |
|----------|-------------|
| **Max Sharpe** | Highest risk-adjusted return (most common choice) |
| **Min Volatility** | Lowest possible portfolio volatility |
| **Max Quadratic Utility** | Custom return vs risk trade-off (affected by risk aversion slider) |
| **Efficient Return** | Minimize risk for a target return |
| **Efficient Risk** | Maximize return for a target risk level |
| **Max Return Min Risk** | Regularized Sharpe with L2 penalty (more diversified than Max Sharpe) |

#### Downside Risk Methods
| Strategy | Description |
|----------|-------------|
| **Min CVaR** | Minimize expected loss in worst 5% of days |
| **Min Semivariance** | Minimize downside volatility only |
| **Semivariance Utility** | Quadratic utility under semivariance model |

#### Alternative Methods
| Strategy | Description |
|----------|-------------|
| **HRP** | Hierarchical Risk Parity — cluster-based diversification, no return estimates needed |
| **Kelly Criterion** | Optimal position sizing for maximum compounding |

### Best Strategy Spotlight

Below the ranking, the best strategy gets a spotlight section showing:
- KPI cards (Total Return, CAGR, Sharpe, Max Drawdown)
- Allocation breakdown with visual bars
- Pie chart of the optimal weights

### Efficient Frontier

An interactive chart showing:
- **Curve**: The efficient frontier — best possible return for each risk level
- **Colored dots**: Individual assets
- **Markers**: Strategy points (star, diamond, hexagon, etc.)

#### Controls
- **Color strategy points by**: Map a metric (Sharpe, Sortino, Calmar, etc.) to the labels
- **Show optimal points**: Select which strategy points to display

### Detailed Expanders
- **Allocation Comparison**: Grouped bar chart comparing weights across all strategies
- **Full Metrics Table**: Complete metrics table for all strategies plus Equal Weight baseline
- **Equity Curves**: How $10k would have grown under each strategy

## Tab 2: Single Strategy

Run one specific optimization strategy with fine-grained control.

### Configuration
1. **Optimize for**: Select a strategy from the dropdown
2. **Target value** (if applicable):
   - For **efficient_return**: Set target annual return (%)
   - For **efficient_risk**: Set target annual volatility (%)
3. Click **Optimize** (or **Find Best Mix** in Beginner mode)

### Results
- Optimal allocation with visual bars and pie chart
- Portfolio performance KPIs (Total Return, CAGR, Sharpe, Sortino, Calmar, Max Drawdown, Volatility)

**Weights are saved** for use in Backtest and Simulate pages.

## Tab 3: Custom Views & Sizing

### Black-Litterman Model

Start from market equilibrium and overlay your personal return expectations.

**How it works**:
1. Set your expected annual return (%) for each asset
2. Set your confidence level (standard deviation) for each view — lower = more confident
3. Choose the optimization target (Max Sharpe, Min Volatility, or Max Quadratic Utility)
4. Click **Run Black-Litterman**

**Tips**:
- If you're unsure about an asset, set a high confidence value (e.g., 0.10+) — the model will rely more on market equilibrium
- If you have a strong conviction, set a low confidence value (e.g., 0.01-0.03)
- Leave expected return at 0 for assets you have no view on

### Kelly Criterion

Computes the mathematically optimal position size for maximum long-term growth.

**Formula**: `Kelly % = Mean Annual Return / Variance of Annual Return`

**Important**: Kelly weights can be aggressive. Many practitioners use **half-Kelly** (divide weights by 2) for a more conservative approach.

Click **Compute Kelly Weights** to see the allocation.

## Saved Portfolio

At the bottom of the page, the **Recommended Portfolio** section shows metrics for the last saved optimization result. This portfolio is automatically loaded in the Backtest and Simulate pages.

## Exporting Data

- **optimization_comparison.csv**: Full metrics table from All Strategies tab

## Tips

- **Start with Max Sharpe** — it's the most commonly used strategy
- **If it concentrates in one asset**, try Max Return Min Risk (regularized) or HRP
- **Black-Litterman is powerful** when you have informed views on specific assets
- **Kelly Criterion is aggressive** — consider half-Kelly for real portfolios
- **Re-run with different risk aversion** to see how the allocation shifts
- The efficient frontier shows whether your assets can form an efficient portfolio at all — if the frontier is very short, your assets are too similar

---

[Back to Documentation](../README.md) | [Previous: Risk Metrics Guide](risk-metrics-guide.md) | [Next: Backtest Guide](backtest-guide.md)
