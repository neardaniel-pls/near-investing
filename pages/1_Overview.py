import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui import (
    init_shared_state, render_workflow_stepper,
    render_next_button, render_portfolio_info,
)

st.set_page_config(page_title="Overview", layout="wide")
init_shared_state()
render_workflow_stepper(1)

st.title("Overview — Data & Exploration")

if "returns" not in st.session_state:
    st.markdown(
        '<div style="text-align:center; padding:60px 20px;">'
        '<p style="color:#aaa; font-size:1.1em;">Go to the <b>main page</b> to fetch your portfolio data first.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    if st.button("Go to Home", use_container_width=True, type="primary"):
        st.switch_page("app.py")
    st.stop()

prices = st.session_state["prices"]
returns = st.session_state["returns"]
tickers = st.session_state.get("tickers", [])

tab_prices, tab_returns, tab_corr, tab_raw = st.tabs(
    ["Normalized Prices", "Returns", "Correlation", "Raw Data"]
)

with tab_prices:
    st.caption("All prices rebased to 100 so you can compare performance across very different assets (e.g. a $50 stock vs a $50,000 crypto).")
    normalized = prices / prices.iloc[0] * 100
    fig = go.Figure()
    for col in normalized.columns:
        fig.add_trace(go.Scatter(x=normalized.index, y=normalized[col], name=col, mode="lines"))
    fig.update_layout(
        title="Normalized Prices (Base = 100)",
        yaxis_title="Price (normalized)", xaxis_title="Date",
        template="plotly_dark", height=600,
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig, use_container_width=True)

with tab_returns:
    st.caption("Left: daily percentage returns over time. Right: how those returns are distributed — a taller, narrower bell curve means more predictable returns.")
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Returns Over Time", "Distribution"))
    for col in returns.columns:
        fig.add_trace(go.Scatter(x=returns.index, y=returns[col], name=col, mode="lines", opacity=0.6), row=1, col=1)
    for col in returns.columns:
        fig.add_trace(go.Histogram(x=returns[col], name=col, opacity=0.5, nbinsx=100), row=1, col=2)
    fig.update_layout(template="plotly_dark", height=500, barmode="overlay",
                      legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Summary Statistics")
    st.caption("count = number of trading days, mean = average daily return, std = daily volatility, min/max = worst/best single day.")
    summary = returns.describe()
    st.dataframe(summary.style.format("{:.6f}"), use_container_width=True)
    csv = summary.to_csv()
    st.download_button("Download CSV", csv, "returns_summary.csv", "text/csv")

with tab_corr:
    st.caption("How assets move together. **+1** = move in lockstep, **0** = no relationship, **-1** = move in opposite directions. Diversification works best with low/negative correlations.")
    corr = returns.corr()
    fig = go.Figure(go.Heatmap(
        z=corr.values, x=corr.columns, y=corr.index,
        colorscale="RdBu", zmin=-1, zmax=1,
        text=corr.values.round(3), texttemplate="%{text}",
    ))
    fig.update_layout(title="Returns Correlation Matrix", template="plotly_dark", height=500)
    st.plotly_chart(fig, use_container_width=True)

with tab_raw:
    st.subheader("Raw Prices")
    st.caption("The actual closing prices downloaded from Yahoo Finance.")
    st.dataframe(prices, use_container_width=True)
    csv = prices.to_csv()
    st.download_button("Download Prices CSV", csv, "prices.csv", "text/csv")

st.markdown("---")
render_next_button("Risk Metrics", "2_Risk_Metrics.py")
