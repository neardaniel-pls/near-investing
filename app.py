import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data import fetch_prices, compute_returns, clear_cache, fetch_ticker_names
from src.config import load_config, update_config
from src.ui import init_shared_state, render_workflow_stepper, render_portfolio_info
from src.metrics import annualized_return, annualized_volatility, sharpe_ratio, max_drawdown, cagr
from src.portfolio import build_portfolio_returns

st.set_page_config(page_title="NEAR Investing", layout="wide", initial_sidebar_state="expanded")
init_shared_state()

PRESET_TICKERS = {
    "Balanced Mix": ["AAPL", "MSFT", "VWCE.MI", "AGGH.AS", "BTC-USD", "^GSPC"],
    "US Tech Giants": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"],
    "Dividend & Value": ["VHYL.AS", "FUSD.DE", "BRK-B", "JPM", "PG", "KO"],
    "European ETFs": ["VWCE.MI", "SXR8.DE", "IWDA.AS", "AGGH.AS", "XDWL.DE", "MEUD.PA"],
    "All-World ETFs": ["VWCE.MI", "VWRL.L", "IWDA.AS", "EUNL.DE", "WEBN.MI"],
    "Crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "AVAX-USD"],
    "60/40 Classic": ["VWCE.MI", "AGGH.AS", "^GSPC"],
    "Golden Butterfly": ["VWCE.MI", "EUNL.DE", "AGGH.AS", "SGLN.L", "XEON.DE"],
    "Custom": [],
}

cfg = load_config()

with st.sidebar:
    st.header("Portfolio Configuration")
    preset = st.selectbox("Preset", list(PRESET_TICKERS.keys()),
                          index=list(PRESET_TICKERS.keys()).index("Balanced Mix")
                          if "Balanced Mix" in PRESET_TICKERS else 0)

    if preset == "Custom":
        default_tickers = "\n".join(cfg.get("tickers", ["AAPL", "VWCE.MI", "BTC-USD", "^GSPC"]))
        ticker_input = st.text_area("Tickers (one per line)", value=default_tickers)
    else:
        ticker_input = st.text_area("Tickers (one per line)", value="\n".join(PRESET_TICKERS[preset]))

    st.caption(
        "Look up tickers at [finance.yahoo.com](https://finance.yahoo.com/lookup) — "
        "use the **Symbol** column exactly as shown (e.g. `VWCE.MI`, `BTC-USD`, `^GSPC`)."
    )

    yesterday = pd.Timestamp.now().normalize() - pd.Timedelta(days=1)
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start", value=pd.Timestamp(cfg.get("start_date", "2018-01-01")))
    end_date = col2.date_input("End", value=yesterday)

    use_cache = st.checkbox("Use cache (1-day TTL)", value=True,
                            help="Cache fetched data locally for 1 day so you don't re-download on every page load.")

    rf_rate = st.number_input("Risk-free rate (%)", value=cfg.get("risk_free_rate", 4.0),
                              min_value=0.0, max_value=20.0, step=0.5, key="global_rf",
                              help="The annual return on a risk-free asset (e.g. government bonds). Used as the baseline for Sharpe, Sortino, Treynor ratios. A typical value is 4-5%.")
    st.session_state["risk_free_rate"] = rf_rate / 100

    initial_inv = st.number_input("Initial investment ($)", value=cfg.get("initial_investment", 10000),
                                  min_value=100, step=1000, key="global_inv",
                                  help="Starting capital for backtesting and equity curves.")
    st.session_state["initial_investment"] = initial_inv

    fetch_btn = st.button("Fetch Data", type="primary", use_container_width=True)

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

    if st.button("Clear Cache"):
        removed = clear_cache()
        st.success(f"Cleared {removed} cache files")

    render_portfolio_info()

render_workflow_stepper(0)

if fetch_btn or "prices" in st.session_state:
    if fetch_btn:
        tickers = [t.strip().upper() for t in ticker_input.strip().split("\n") if t.strip()]
        with st.spinner("Fetching data from Yahoo Finance..."):
            prices = fetch_prices(
                tickers, start=str(start_date), end=str(end_date), use_cache=use_cache,
            )
        if prices.empty:
            st.error("No data fetched. Check your tickers and date range.")
            st.stop()
        returns = compute_returns(prices)
        with st.spinner("Resolving ticker names..."):
            ticker_names = fetch_ticker_names(tickers)
        st.session_state["prices"] = prices
        st.session_state["returns"] = returns
        st.session_state["tickers"] = tickers
        st.session_state["ticker_names"] = ticker_names
        st.success(f"Loaded **{len(prices)}** trading days for **{len(tickers)}** assets")

    prices = st.session_state.get("prices")
    returns = st.session_state.get("returns")
    tickers = st.session_state.get("tickers", [])

    if prices is None:
        st.warning("Click **Fetch Data** to load your portfolio.")
        st.stop()

    st.title("Dashboard")
    st.markdown("---")

    rf = st.session_state.get("risk_free_rate", 0.04)
    equal_w = {t: 1.0 / len(tickers) for t in tickers}
    port_ret = build_portfolio_returns(prices, equal_w)
    port_ann_ret = annualized_return(port_ret)
    port_vol = annualized_volatility(port_ret)
    port_sharpe = sharpe_ratio(port_ret, rf=rf)
    port_mdd = max_drawdown(port_ret)
    port_cagr = cagr(port_ret)
    total_return = (1 + port_ret).prod() - 1

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.metric("Total Return", f"{total_return:.2%}",
                   delta=f"on ${st.session_state.get('initial_investment', 10000):,.0f}",
                   help="Cumulative return of an equal-weight portfolio from start to end date.")
    with kpi2:
        st.metric("CAGR", f"{port_cagr:.2%}",
                   help="Compound Annual Growth Rate — the annualized return assuming compounding.")
    with kpi3:
        st.metric("Sharpe Ratio", f"{port_sharpe:.3f}",
                   help="Risk-adjusted return. (Return - Risk-free rate) / Volatility. Above 1.0 is good, above 2.0 is excellent.")
    with kpi4:
        st.metric("Volatility", f"{port_vol:.2%}",
                   help="Annualized standard deviation of daily returns. Higher = more unpredictable swings.")
    with kpi5:
        st.metric("Max Drawdown", f"{port_mdd:.2%}", delta_color="inverse",
                   help="Largest peak-to-trough decline. If -30%, your portfolio lost 30% from its highest point.")

    st.markdown("---")

    col_chart, col_assets = st.columns([3, 2])

    with col_chart:
        st.subheader("Normalized Performance")
        ticker_names = st.session_state.get("ticker_names", {})
        normalized = prices / prices.iloc[0] * 100
        fig = go.Figure()
        for col in normalized.columns:
            label = f"{col} — {ticker_names.get(col, col)}"
            fig.add_trace(go.Scatter(x=normalized.index, y=normalized[col], name=label, mode="lines"))
        fig.update_layout(
            yaxis_title="Normalized (Base=100)", xaxis_title="Date",
            template="plotly_dark", height=400, margin=dict(l=40, r=20, t=30, b=40),
            legend=dict(orientation="h", y=1.12),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_assets:
        st.subheader("Asset Rankings")
        asset_data = []
        for t in tickers:
            r = returns[t]
            asset_data.append({
                "Ticker": t,
                "Name": ticker_names.get(t, ""),
                "Return": f"{annualized_return(r):.2%}",
                "Volatility": f"{annualized_volatility(r):.2%}",
                "Sharpe": f"{sharpe_ratio(r, rf=rf):.3f}",
                "Max DD": f"{max_drawdown(r):.2%}",
            })
        asset_df = pd.DataFrame(asset_data)
        st.dataframe(asset_df, use_container_width=True, hide_index=True, height=min(400, 50 + len(tickers) * 35))

    st.markdown("---")
    st.subheader("Quick Navigation")
    nav1, nav2, nav3, nav4, nav5 = st.columns(5)
    with nav1:
        if st.button("Risk Metrics", use_container_width=True):
            st.switch_page("pages/2_Risk_Metrics.py")
    with nav2:
        if st.button("Backtest", use_container_width=True):
            st.switch_page("pages/3_Backtest.py")
    with nav3:
        if st.button("Optimization", use_container_width=True):
            st.switch_page("pages/4_Optimization.py")
    with nav4:
        if st.button("Monte Carlo", use_container_width=True):
            st.switch_page("pages/5_Monte_Carlo.py")
    with nav5:
        if st.button("Rolling Opt.", use_container_width=True):
            st.switch_page("pages/6_Rolling_Optimization.py")

else:
    st.markdown(
        '<div style="text-align:center; padding:60px 20px;">'
        '<h1>NEAR Investing</h1>'
        '<p style="color:#aaa; font-size:1.2em;">Portfolio Analysis & Optimization Tool</p>'
        '<p style="color:#888;">Configure your portfolio in the sidebar and click <b>Fetch Data</b> to get started.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
