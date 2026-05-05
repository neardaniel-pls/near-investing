import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="NEAR Investing", layout="wide", initial_sidebar_state="expanded")

st.title("NEAR Investing")
st.subheader("Portfolio Analysis & Optimization Tool")
st.markdown("---")

st.markdown("""
Welcome! Use the sidebar to navigate between sections:

1. **Overview** — Fetch data, view normalized prices, returns distribution, and correlation
2. **Risk Metrics** — Full risk/return metrics table, rolling charts, drawdowns
3. **Backtest** — Build portfolios, compare allocations, equity curves
4. **Optimization** — Choose optimization target, Black-Litterman, Kelly, efficient frontier
5. **Monte Carlo** — Stress-test portfolios with simulated scenarios
6. **Rolling Optimization** — Walk-forward analysis, weights over time
""")

st.info("Start by entering tickers in the **Overview** page. Data will be shared across all pages via session state.")
