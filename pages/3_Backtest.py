import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.portfolio import (
    build_portfolio_returns, equity_curve, drawdown_series,
    rebalanced_portfolio_returns, compare_portfolios,
)
from src.metrics import metrics_table

st.set_page_config(page_title="Backtest", layout="wide")
st.title("Portfolio Backtest")

if "returns" not in st.session_state:
    st.warning("Go to **Overview** first to fetch data.")
    st.stop()

prices = st.session_state["prices"]
returns = st.session_state["returns"]
tickers = st.session_state.get("tickers", [])

with st.sidebar:
    st.header("Portfolio Allocation")
    st.markdown("Set weights for each asset (must sum to 100%)")
    weights = {}
    default_weights = {"^GSPC": 20, "BTC-USD": 10}
    for t in tickers:
        default = default_weights.get(t, round(70 / max(len(tickers) - len(default_weights), 1)))
        w = st.slider(f"{t}", 0, 100, default, key=f"w_{t}")
        weights[t] = w / 100

    total_w = sum(weights.values())
    if abs(total_w - 1.0) > 0.01:
        st.error(f"Weights sum to {total_w:.0%}. Must be 100%.")
    else:
        normalized_weights = {k: v / total_w for k, v in weights.items()}

    rebalance_freq = st.selectbox("Rebalance frequency", ["None (Buy & Hold)", "Monthly", "Quarterly", "Yearly"])
    initial_value = st.number_input("Initial investment ($)", value=10000, min_value=100, step=1000)

    st.markdown("---")
    st.header("Compare Allocations")
    compare_mode = st.checkbox("Compare multiple allocations")

tab_main, tab_metrics, tab_yearly = st.tabs(["Equity Curve & Drawdown", "Metrics Comparison", "Yearly Returns"])

if abs(total_w - 1.0) > 0.01:
    st.stop()

freq_map = {"None (Buy & Hold)": None, "Monthly": "M", "Quarterly": "Q", "Yearly": "Y"}
freq = freq_map[rebalance_freq]

portfolio_rets = build_portfolio_returns(prices, normalized_weights)
if freq:
    rebal_rets = rebalanced_portfolio_returns(prices, normalized_weights, rebalance_freq=freq)
else:
    rebal_rets = portfolio_rets

benchmark_ticker = [t for t in tickers if t.startswith("^")]
bench_rets = returns[benchmark_ticker[0]] if benchmark_ticker else None

with tab_main:
    portfolios_to_plot = {
        "Buy & Hold": portfolio_rets,
    }
    if freq:
        portfolios_to_plot[f"Rebalanced ({rebalance_freq})"] = rebal_rets
    if bench_rets is not None:
        portfolios_to_plot[benchmark_ticker[0]] = bench_rets

    curves = compare_portfolios(portfolios_to_plot, initial_value=initial_value)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=("Equity Curve", "Drawdown"), vertical_spacing=0.08)
    for col in curves.columns:
        fig.add_trace(go.Scatter(x=curves.index, y=curves[col], name=col, mode="lines"), row=1, col=1)
    for name, ret in portfolios_to_plot.items():
        dd = drawdown_series(ret) * 100
        fig.add_trace(go.Scatter(x=dd.index, y=dd, name=f"{name} DD", mode="lines"), row=2, col=1)
    fig.update_layout(
        title=f"Portfolio Performance (Initial: ${initial_value:,})",
        template="plotly_white", height=700,
    )
    fig.update_yaxes(title_text="Value ($)", row=1, col=1)
    fig.update_yaxes(title_text="Drawdown %", row=2, col=1)
    st.plotly_chart(fig, use_container_width=True)

with tab_metrics:
    if compare_mode:
        col_alloc1, col_alloc2, col_alloc3 = st.columns(3)
        with col_alloc1:
            st.markdown("**Conservative**")
            conservative = {}
            for t in tickers:
                conservative[t] = st.number_input(f"{t} %", 0, 100, 10 if t != "^GSPC" else 20, key=f"cons_{t}") / 100
        with col_alloc2:
            st.markdown("**Balanced**")
            balanced = {}
            for t in tickers:
                balanced[t] = st.number_input(f"{t} %", 0, 100, round(normalized_weights.get(t, 0) * 100), key=f"bal_{t}") / 100
        with col_alloc3:
            st.markdown("**Aggressive**")
            aggressive = {}
            for t in tickers:
                aggressive[t] = st.number_input(f"{t} %", 0, 100, 40 if "BTC" in t else 20, key=f"agg_{t}") / 100

        alloc_returns = {
            "Conservative": build_portfolio_returns(prices, conservative),
            "Balanced": build_portfolio_returns(prices, balanced),
            "Aggressive": build_portfolio_returns(prices, aggressive),
            "Buy & Hold": portfolio_rets,
        }
        if bench_rets is not None:
            alloc_returns[benchmark_ticker[0]] = bench_rets
    else:
        alloc_returns = {"Buy & Hold": portfolio_rets}
        if freq:
            alloc_returns[f"Rebalanced ({rebalance_freq})"] = rebal_rets
        if bench_rets is not None:
            alloc_returns[benchmark_ticker[0]] = bench_rets

    table = metrics_table(alloc_returns, benchmark_returns=bench_rets)
    st.dataframe(table.style.format("{:.4f}"), use_container_width=True, height=400)

    alloc_curves = compare_portfolios(alloc_returns, initial_value=initial_value)
    fig = go.Figure()
    for col in alloc_curves.columns:
        fig.add_trace(go.Scatter(x=alloc_curves.index, y=alloc_curves[col], name=col, mode="lines"))
    fig.update_layout(
        title="Allocation Comparison", yaxis_title="Value ($)", xaxis_title="Date",
        template="plotly_white", height=600,
    )
    st.plotly_chart(fig, use_container_width=True)

with tab_yearly:
    yearly = {}
    for name, ret in alloc_returns.items():
        yearly[name] = ret.groupby(ret.index.year).apply(lambda x: (1 + x).prod() - 1)
    yearly_df = pd.DataFrame(yearly)

    fig = go.Figure(go.Heatmap(
        z=yearly_df.values * 100, x=yearly_df.columns, y=yearly_df.index,
        colorscale="RdYlGn", text=yearly_df.values.round(2) * 100,
        texttemplate="%{text:.1f}%",
    ))
    fig.update_layout(title="Annual Returns (%)", template="plotly_white", height=max(400, len(yearly_df) * 40 + 200))
    st.plotly_chart(fig, use_container_width=True)
