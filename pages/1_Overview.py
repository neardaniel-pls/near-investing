import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.data import fetch_prices, compute_returns, clear_cache

st.set_page_config(page_title="Overview", layout="wide")
st.title("Overview — Data Fetching & Exploration")

PRESET_TICKERS = {
    "US Tech Stocks": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
    "European ETFs": ["VWCE.MI", "SXR8.DE", "IWDA.AS", "Xtrackers_MSCI_World_UCITS_ETF.XETRA"],
    "Crypto": ["BTC-USD", "ETH-USD", "SOL-USD"],
    "Balanced Mix": ["AAPL", "VWCE.MI", "BTC-USD", "^GSPC"],
    "Custom": [],
}

with st.sidebar:
    st.header("Configuration")
    preset = st.selectbox("Preset portfolios", list(PRESET_TICKERS.keys()), index=3)
    if preset == "Custom":
        ticker_input = st.text_area("Tickers (one per line)", value="AAPL\nVWCE.MI\nBTC-USD\n^GSPC")
    else:
        ticker_input = st.text_area("Tickers (one per line)", value="\n".join(PRESET_TICKERS[preset]))

    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start date", value=pd.Timestamp("2018-01-01"))
    end_date = col2.date_input("End date", value=pd.Timestamp("2025-01-01"))

    use_cache = st.checkbox("Use cache (1-day TTL)", value=True)
    fetch_btn = st.button("Fetch Data", type="primary", use_container_width=True)

    if st.button("Clear Cache"):
        removed = clear_cache()
        st.success(f"Cleared {removed} cache files")

if fetch_btn or "prices" in st.session_state:
    if fetch_btn:
        tickers = [t.strip().upper() for t in ticker_input.strip().split("\n") if t.strip()]
        with st.spinner("Fetching data from Yahoo Finance..."):
            prices = fetch_prices(
                tickers,
                start=str(start_date),
                end=str(end_date),
                use_cache=use_cache,
            )
        if prices.empty:
            st.error("No data fetched. Check your tickers and date range.")
            st.stop()
        returns = compute_returns(prices)
        st.session_state["prices"] = prices
        st.session_state["returns"] = returns
        st.session_state["tickers"] = tickers
        st.success(f"Fetched {len(prices)} trading days for {len(tickers)} assets")

    prices = st.session_state.get("prices")
    returns = st.session_state.get("returns")
    tickers = st.session_state.get("tickers", [])

    if prices is None:
        st.warning("Click 'Fetch Data' to load asset prices.")
        st.stop()

    tab_prices, tab_returns, tab_corr, tab_raw = st.tabs(["Normalized Prices", "Returns", "Correlation", "Raw Data"])

    with tab_prices:
        normalized = prices / prices.iloc[0] * 100
        fig = go.Figure()
        for col in normalized.columns:
            fig.add_trace(go.Scatter(x=normalized.index, y=normalized[col], name=col, mode="lines"))
        fig.update_layout(
            title="Normalized Prices (Base = 100)",
            yaxis_title="Price (normalized)", xaxis_title="Date",
            template="plotly_white", height=600,
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab_returns:
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Returns Over Time", "Distribution"))
        for col in returns.columns:
            fig.add_trace(go.Scatter(x=returns.index, y=returns[col], name=col, mode="lines", opacity=0.6), row=1, col=1)
        for col in returns.columns:
            fig.add_trace(go.Histogram(x=returns[col], name=col, opacity=0.5, nbinsx=100), row=1, col=2)
        fig.update_layout(template="plotly_white", height=500, barmode="overlay")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Returns Summary Statistics")
        st.dataframe(returns.describe().style.format("{:.6f}"), use_container_width=True)

    with tab_corr:
        corr = returns.corr()
        fig = go.Figure(go.Heatmap(
            z=corr.values, x=corr.columns, y=corr.index,
            colorscale="RdBu", zmin=-1, zmax=1,
            text=corr.values.round(3), texttemplate="%{text}",
        ))
        fig.update_layout(title="Returns Correlation Matrix", template="plotly_white", height=500)
        st.plotly_chart(fig, use_container_width=True)

    with tab_raw:
        st.subheader("Raw Prices (last 20 rows)")
        st.dataframe(prices.tail(20), use_container_width=True)
