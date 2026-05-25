# Quick Start Guide

Get up and running with NEAR Investing in 5 minutes.

## Prerequisites

- Python 3.11+
- pip
- Internet connection (for Yahoo Finance data)

## Setup (2 minutes)

### Step 1: Clone and Enter Project
```bash
git clone https://github.com/neardaniel-pls/near-investing.git
cd near-investing
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

## Launch (30 seconds)

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## First Analysis (2 minutes)

### Step 1: Choose Investments
In the sidebar, pick a preset (e.g., "Balanced Mix") or enter your own tickers (one per line).

Look up tickers at [finance.yahoo.com/lookup](https://finance.yahoo.com/lookup) — use the **Symbol** column exactly as shown (e.g., `VWCE.MI`, `BTC-USD`, `^GSPC`).

### Step 2: Set Date Range
Choose how far back to analyze. The app suggests a good start date for each preset.

### Step 3: Fetch Data
Click **"Fetch Data"** in the sidebar. Data is cached locally for 1 day so you don't re-download on every page load.

### Step 4: Explore
Navigate through the workflow:
1. **Dashboard** — KPIs, prices, returns, correlation
2. **Risk** — Sharpe, Sortino, drawdowns, rolling metrics
3. **Optimize** — Find optimal weights using 10+ strategies
4. **Backtest** — Test allocations with buy-and-hold or rebalancing
5. **Simulate** — Monte Carlo and walk-forward simulations

## Quick Try with Sample Data

Don't want to pick tickers? Click **"Try with Sample Portfolio (Balanced Mix)"** on the home page to load a preset and explore immediately.

## UI Modes

Toggle between **Beginner** and **Advanced** mode in the sidebar:
- **Beginner** — Simplified labels and explanations (e.g., "Price Swings" instead of "Annualized Volatility")
- **Advanced** — Standard financial terminology with technical descriptions

## Configuration (Optional)

Click **"Save as Default"** in the sidebar to persist your tickers, date range, risk-free rate, and initial investment. Settings are saved to `data/user_config.json`.

## Next Steps

1. **Read Detailed Guides**: Check [docs/guides/](guides/) for each page
2. **Jupyter Notebooks**: Explore `notebooks/` for programmatic analysis
3. **Customize**: Adjust risk-free rate, initial investment, and simulation parameters

## Need Help?

- **Quick Answers**: [FAQ](FAQ.md)
- **Detailed Usage**: [Guides](guides/)
- **Issues**: [Report a Bug](https://github.com/neardaniel-pls/near-investing/issues/new?template=bug_report.md)

---

**Last Updated**: 2026-05-25
