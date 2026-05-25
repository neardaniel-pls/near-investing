# Simulation Guide

The Simulate page provides two powerful analysis tools: Monte Carlo simulation for stress-testing your portfolio, and walk-forward optimization for realistic strategy validation.

## Accessing the Simulate Page

1. Fetch data on the home page
2. Navigate to **Simulate** (fifth page in the workflow)

## Overview

The page has two tabs:

1. **Monte Carlo** — Generate thousands of possible future scenarios
2. **Walk-Forward** — Test your strategy in realistic rolling-window mode

---

## Tab 1: Monte Carlo

Monte Carlo simulation generates thousands of possible future scenarios to stress-test your portfolio.

### Setting Weights

In the sidebar, set allocation weights (same interface as Backtest). If you ran optimization, weights are auto-loaded.

### Simulation Methods

| Method | Description | Best For |
|--------|-------------|----------|
| **Historical Bootstrap** | Randomly samples from actual past daily returns | Realistic scenarios — captures crashes, fat tails, and real patterns |
| **Parametric** | Assumes returns follow a normal distribution | Quick estimates — underestimates extreme events |

**Recommendation**: Use Historical Bootstrap for realistic results. Parametric is useful as a comparison baseline.

### Configuration

| Setting | Options | Default | Description |
|---------|---------|---------|-------------|
| **Simulation period** | 3 months, 6 months, 1 year, 2 years, 5 years | 1 year | How far into the future to simulate |
| **Number of simulations** | 1,000 / 5,000 / 10,000 / 50,000 | 10,000 | More paths = more accurate but slower |
| **Simulation method** | Historical / Parametric | Historical | How to generate random returns |
| **Seed** | Any integer | 42 | Fixed seed = reproducible results |

### Summary KPIs

| KPI | Description |
|-----|-------------|
| **Expected Value** | Average final portfolio value across all simulations |
| **95% Range** | Range from 5th to 95th percentile — "95% chance your portfolio lands between these values" |
| **Probability of Loss** | % of scenarios where you end with less than you started |
| **Probability of >50% Loss** | % of scenarios where you lose more than half |

### Simulated Paths Chart

The main visualization shows:
- **Faded lines**: Up to 200 individual simulated paths
- **Green dashed line**: Best 5% of scenarios
- **Solid teal line**: Average path
- **Red dashed line**: Worst 5% of scenarios
- **Gray dashed line**: Initial investment (breakeven)

### Detailed Statistics

Expand **"Detailed Statistics"** for:
- **Value Statistics**: Median, Std, VaR (95%), CVaR (95%), Min/Max final values
- **Return Statistics**: Mean/Median return, VaR/CVaR of returns, Avg/Worst Max Drawdown, Probability of Loss

### Final Value Distribution

A histogram of ending portfolio values across all simulated paths. The red dashed line marks your initial investment.

- More area to the right of the red line = higher chance of profit
- A long left tail = significant crash risk

### Method Comparison

Expand **"Compare Different Methods"** to see Historical Bootstrap vs Parametric side by side. Large differences indicate that the normal distribution assumption is a poor fit (common for crypto and volatile assets).

### Stress-Test Multiple Allocations

Expand **"Compare Allocations Under Stress"** to define 2-5 custom allocations and run Monte Carlo on each. Compare:
- Mean return, Std return
- Average max drawdown
- Probability of loss

This lets you see which allocation performs best under stress.

---

## Tab 2: Walk-Forward

Walk-forward optimization tests your strategy as if you were using it in real-time — a more realistic alternative to simple backtesting.

### How It Works

1. **Train**: Optimize weights on a past window (e.g., the last 252 trading days ≈ 1 year)
2. **Test**: Apply those weights to the next period (e.g., the next 21 days ≈ 1 month)
3. **Roll Forward**: Move the window ahead and repeat

### Configuration (Sidebar)

| Setting | Options | Default | Description |
|---------|---------|---------|-------------|
| **Optimization target** | All strategies | Max Sharpe | Strategy to use in each window |
| **Training window** | 126 / 252 / 504 / 756 days | 252 | How much past data to learn from |
| **Test window** | 5 / 21 / 42 / 63 days | 21 | How far ahead to test |
| **Rebalance step** | 5 / 21 / 42 / 63 days | 21 | How often to re-optimize |

### Results KPIs

| KPI | Description |
|-----|-------------|
| **Avg Train Sharpe** | Average in-sample Sharpe ratio — how good the optimization looked on past data |
| **Avg Test Return** | Average out-of-sample return — what actually happened |
| **Test Win Rate** | Percentage of test periods with positive returns |

A large gap between Train Sharpe and Test Return suggests overfitting.

### Weights Over Time

A stacked area chart showing how the optimizer's allocation changed over time. Large swings suggest sensitivity to the data window. Stable weights suggest a robust allocation.

### Walk-Forward Equity Curve

Cumulative performance if you had followed this strategy vs a static equal-weight benchmark.

### Train vs Test Performance

A dual-panel bar chart:
- **Top**: In-sample Sharpe for each window
- **Bottom**: Out-of-sample return for each window (green = positive, red = negative)

Look for patterns: if test returns are consistently negative, the strategy doesn't generalize.

### Multi-Strategy Comparison

Expand **"Compare Multiple Strategies"** to run several strategies side by side in walk-forward mode.

1. Select strategies (e.g., Max Sharpe, Min Volatility, HRP)
2. Click **Compare Strategies**
3. Results are ranked by your chosen metric (WF Sharpe, WF Total Return, etc.)
4. The best strategy's latest weights are saved for use in simulations

### Saved Portfolio

The best rolling strategy's latest weights are saved as the recommended portfolio, shown at the bottom of the page.

## Tips

- **Monte Carlo** answers "what could happen?" — use it for risk assessment
- **Walk-Forward** answers "would my strategy have worked?" — use it for strategy validation
- **Historical Bootstrap > Parametric** for realistic risk assessment
- **More simulations = more accurate** but 10,000 is usually sufficient
- Walk-forward results are more reliable than simple backtests because they avoid look-ahead bias
- Compare multiple strategies in walk-forward to find the most robust approach
- A strategy with lower Train Sharpe but higher Test Return may be more robust than one that overfits the training data

---

[Back to Documentation](../README.md) | [Previous: Backtest Guide](backtest-guide.md)
