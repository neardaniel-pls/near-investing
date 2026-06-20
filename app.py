import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data import fetch_prices, compute_returns, clear_cache, fetch_ticker_names
from src.config import load_config, update_config
from src.optimization import optimize_portfolio
from src.ui import (
    init_shared_state, render_workflow_stepper, render_portfolio_info,
    render_mode_toggle, is_beginner, load_sample_portfolio,
    save_recommended_weights,
)
from src.styles import inject_global_styles, divider

st.set_page_config(page_title="NEAR Investing", layout="wide", initial_sidebar_state="expanded")
inject_global_styles()
init_shared_state()

PRESET_TICKERS = {
    "Balanced Mix": ["AAPL", "MSFT", "VWCE.MI", "AGGH.AS", "BTC-USD", "^GSPC"],
    "Long History (EU)": ["IWDA.AS", "EUNL.DE", "^GSPC", "^STOXX50E", "GLD", "XEON.DE"],
    "US Tech Giants": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"],
    "Dividend & Value": ["VHYL.AS", "FUSD.DE", "BRK-B", "JPM", "PG", "KO"],
    "European ETFs": ["VWCE.MI", "SXR8.DE", "IWDA.AS", "AGGH.AS", "XDWL.DE", "MEUD.PA"],
    "All-World ETFs": ["VWCE.MI", "VWRL.L", "IWDA.AS", "EUNL.DE"],
    "Crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "AVAX-USD"],
    "60/40 Classic": ["VWCE.MI", "AGGH.AS", "^GSPC"],
    "Golden Butterfly": ["VWCE.MI", "EUNL.DE", "AGGH.AS", "SGLN.L", "XEON.DE"],
    "Custom": [],
}

PRESET_SUGGESTED_START = {
    "Balanced Mix": "2019-06-01",
    "Long History (EU)": "2010-01-01",
    "US Tech Giants": "2010-01-01",
    "Dividend & Value": "2020-01-01",
    "European ETFs": "2019-06-01",
    "All-World ETFs": "2013-01-01",
    "Crypto": "2020-01-01",
    "60/40 Classic": "2019-06-01",
    "Golden Butterfly": "2019-06-01",
    "Custom": None,
}

cfg = load_config()

with st.sidebar:
    render_mode_toggle()
    st.markdown("---")

    setup_label = "\U0001f4cb Portfolio Setup" if not is_beginner() else "\U0001f4cb Choose Your Investments"
    with st.expander(setup_label, expanded=True):
        preset = st.selectbox("Preset", list(PRESET_TICKERS.keys()),
                              index=list(PRESET_TICKERS.keys()).index("Balanced Mix")
                              if "Balanced Mix" in PRESET_TICKERS else 0)

        if preset == "Custom":
            default_tickers = "\n".join(cfg.get("tickers", ["AAPL", "VWCE.MI", "BTC-USD", "^GSPC"]))
            ticker_input = st.text_area("Tickers (one per line)", value=default_tickers)
        else:
            ticker_input = st.text_area("Tickers (one per line)", value="\n".join(PRESET_TICKERS[preset]))

        st.caption(
            "Look up tickers at [finance.yahoo.com](https://finance.yahoo.com/lookup) \u2014 "
            "use the **Symbol** column exactly as shown (e.g. `VWCE.MI`, `BTC-USD`, `^GSPC`)."
        )

        yesterday = pd.Timestamp.now().normalize() - pd.Timedelta(days=1)
        suggested = PRESET_SUGGESTED_START.get(preset)
        if suggested and preset != "Custom":
            st.caption(f"\U0001f4c5 Suggested start date for this preset: **{suggested}**")
        col1, col2 = st.columns(2)
        start_date = col1.date_input("Start", value=pd.Timestamp(cfg.get("start_date", "2010-01-01")))
        end_date = col2.date_input("End", value=yesterday)

        fetch_label = "Fetch Data" if not is_beginner() else "Load My Portfolio"
        fetch_btn = st.button(fetch_label, type="primary", use_container_width=True)

    with st.expander("\u2699\ufe0f Parameters" if not is_beginner() else "\u2699\ufe0f Settings", expanded=False):
        rf_help = (
            "The annual return on a risk-free asset (e.g. government bonds). Used for Sharpe, Sortino, Treynor ratios."
            if not is_beginner()
            else "The yearly return on a very safe investment (like government bonds). Usually 4-5%."
        )
        rf_rate = st.number_input(
            "Risk-free rate (%)" if not is_beginner() else "Safe investment return (%)",
            value=cfg.get("risk_free_rate", 4.0),
            min_value=0.0, max_value=20.0, step=0.5, key="global_rf",
            help=rf_help,
        )
        st.session_state["risk_free_rate"] = rf_rate / 100

        inv_help = (
            "Starting capital for backtesting and equity curves."
            if not is_beginner()
            else "How much money you're starting with."
        )
        initial_inv = st.number_input(
            "Initial investment ($)" if not is_beginner() else "Starting amount ($)",
            value=cfg.get("initial_investment", 10000),
            min_value=100, step=1000, key="global_inv",
            help=inv_help,
        )
        st.session_state["initial_investment"] = initial_inv

    with st.expander("\U0001f4be Actions", expanded=False):
        if st.button("Save as Default"):
            tickers_to_save = [t.strip().upper() for t in ticker_input.strip().split("\n") if t.strip()]
            update_config(
                tickers=tickers_to_save,
                start_date=str(start_date),
                end_date=str(end_date),
                risk_free_rate=rf_rate,
                initial_investment=initial_inv,
            )
            st.success("Saved as default!")
            st.toast("Settings saved!", icon="\u2705")

        use_cache = st.checkbox("Use cache (1-day TTL)", value=True,
                                help="Cache fetched data locally for 1 day so you don't re-download on every page load.")

        if st.button("Clear Cache"):
            removed = clear_cache()
            st.success(f"Cleared {removed} cache files")
            st.toast(f"Removed {removed} cached files", icon="\U0001f5d1")

    render_portfolio_info()

render_workflow_stepper(0)

if fetch_btn:
    tickers = [t.strip().upper() for t in ticker_input.strip().split("\n") if t.strip()]
    with st.spinner("Fetching data from Yahoo Finance..."):
        prices = fetch_prices(
            tickers, start=str(start_date), end=str(end_date), use_cache=use_cache,
        )
    if prices.empty:
        st.error(
            "No data fetched. Check your tickers and date range."
            if not is_beginner()
            else "Couldn't load data. Please check that your ticker symbols are correct."
        )
        st.stop()

    dropped = [t for t in tickers if t not in prices.columns]
    if dropped:
        st.warning(f"\u26a0\ufe0f No data found for {len(dropped)} ticker(s); they were skipped: {', '.join(dropped)}")
        tickers = [t for t in tickers if t in prices.columns]

    returns = compute_returns(prices)
    # Auto-recommend a default optimal allocation so the answer is available immediately
    try:
        _rf = st.session_state.get("risk_free_rate", 0.04)
        rec = optimize_portfolio(prices, target="max_sharpe", risk_free_rate=_rf)
        if rec:
            save_recommended_weights(rec, "Auto: Max Sharpe")
    except Exception:
        pass
    with st.spinner("Resolving ticker names..."):
        ticker_names = fetch_ticker_names(tickers)

    # Data availability warning
    requested_start = pd.Timestamp(start_date)
    truncated = []
    for col in prices.columns:
        first_valid = prices[col].first_valid_index()
        if first_valid is not None and first_valid > requested_start:
            truncated.append((col, first_valid.strftime("%Y-%m-%d")))
    if truncated:
        truncated_msgs = [f"**{t}** \u2192 data starts {d}" for t, d in truncated]
        earliest_common = prices.dropna(how="any").index[0] if not prices.dropna(how="any").empty else None
        suggestion = f"\n\nSet start date to **{earliest_common.strftime('%Y-%m-%d')}** to include all tickers." if earliest_common else ""
        st.warning("\u26a0\ufe0f Some tickers have less history than requested:\n\n" + "\n".join(truncated_msgs) + suggestion)

    st.session_state["prices"] = prices
    st.session_state["returns"] = returns
    st.session_state["tickers"] = tickers
    st.session_state["ticker_names"] = ticker_names
    st.toast(f"Loaded {len(tickers)} assets ({len(prices)} days)", icon="\u2705")
    st.switch_page("pages/1_Dashboard.py")

if "prices" in st.session_state:
    st.info("\u2705 Portfolio data loaded. Go to **Dashboard** to explore your portfolio.")
    if st.button("\U0001f3e0 Go to Dashboard", type="primary", use_container_width=True):
        st.switch_page("pages/1_Dashboard.py")
else:
    st.markdown(
        '<div style="text-align:center; padding:40px 20px 20px 20px;">'
        '<h1 style="font-size:2.5rem; margin-bottom:0.3rem; background: linear-gradient(135deg, #00d4aa, #4c78a8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">NEAR Investing</h1>'
        '<p style="color:#aaa; font-size:1.2em; margin-bottom:0;">Portfolio Analysis & Optimization Tool</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:1rem; max-width:600px; margin:1rem auto;">'
        '<div class="step-card">'
        '<div class="step-number">1</div>'
        '<div class="step-title">Choose Investments</div>'
        '<div class="step-desc">Pick a preset or enter your own tickers</div>'
        '</div>'
        '<div class="step-card">'
        '<div class="step-number">2</div>'
        '<div class="step-title">Set Date Range</div>'
        '<div class="step-desc">Choose how far back to analyze</div>'
        '</div>'
        '<div class="step-card">'
        '<div class="step-number">3</div>'
        '<div class="step-title">Load Data</div>'
        '<div class="step-desc">Click Fetch Data in the sidebar</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("")

    feature_cards = [
        ("\U0001f3e0", "Dashboard", "KPIs, prices, returns, correlation, asset rankings"),
        ("\u26a1", "Risk Metrics", "Sharpe, Sortino, drawdowns, rolling metrics"),
        ("\u2699\ufe0f", "Optimization", "Find optimal weights using 10+ strategies"),
        ("\U0001f3af", "Backtest", "Test allocations with buy-and-hold or rebalancing"),
        ("\U0001f3b2", "Simulate", "Monte Carlo and walk-forward simulations"),
    ]

    grid_html = '<div class="feature-grid" style="max-width:900px; margin:0 auto;">'
    for icon, title, desc in feature_cards:
        grid_html += (
            f'<div class="feature-card">'
            f'<div class="feature-icon">{icon}</div>'
            f'<div class="feature-title">{title}</div>'
            f'<div class="feature-desc">{desc}</div>'
            f'</div>'
        )
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

    st.markdown("<div style='text-align:center; margin:1.5rem 0;'>", unsafe_allow_html=True)
    if st.button("\U0001f680 Try with Sample Portfolio (Balanced Mix)", type="primary", use_container_width=False):
        if load_sample_portfolio():
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
