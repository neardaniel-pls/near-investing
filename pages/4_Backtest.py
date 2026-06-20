import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.portfolio import (
    build_portfolio_returns, drawdown_series,
    rebalanced_portfolio_returns, compare_portfolios,
)
from src.metrics import metrics_table
from src.ui import (
    init_shared_state, require_data, render_workflow_stepper,
    render_next_button, render_portfolio_info, render_weight_sliders,
    render_page_header, render_recommended_sidebar_widget,
    is_beginner, label,
)
from src.styles import inject_global_styles, divider, section_title
from src.charts import apply_theme, chart_colors, format_dataframe_styler
from src.export import render_export_section

st.set_page_config(page_title="Backtest", layout="wide")
inject_global_styles()
init_shared_state()
render_workflow_stepper(4)
render_page_header("Backtest")
require_data()

prices = st.session_state["prices"]
returns = st.session_state["returns"]
tickers = st.session_state.get("tickers", [])
initial_value = st.session_state.get("initial_investment", 10000)

rf = st.session_state.get("risk_free_rate", 0.04)

rec_weights = st.session_state.get("recommended_weights")
rec_label = st.session_state.get("recommended_label", "")

with st.sidebar:
    render_portfolio_info()
    render_recommended_sidebar_widget()
    st.markdown("---")

    if rec_weights:
        st.success(f"Optimized: **{rec_label}**")
        default_bt = {t: v * 100 for t, v in rec_weights.items()}
    else:
        default_bt = {}

    weights, weights_valid = render_weight_sliders(
        tickers, key_prefix="bt", default_weights=default_bt,
    )

    if weights_valid:
        st.markdown("---")
        rebal_label = "Rebalance frequency" if not is_beginner() else "How often to rebalance"
        rebal_help = (
            "Buy & Hold = never sell. Rebalancing = periodically sell winners / buy losers to restore your target weights."
            if not is_beginner()
            else "Buy & Hold = invest once and wait. Rebalancing = periodically adjust back to your target mix."
        )
        rebalance_freq = st.selectbox(
            rebal_label,
            ["None (Buy & Hold)", "Monthly", "Quarterly", "Yearly"] if not is_beginner()
            else ["Never (Buy & Hold)", "Monthly", "Quarterly", "Yearly"],
            help=rebal_help,
        )

with st.expander("\u2753 What is backtesting?" if not is_beginner() else "\u2753 What does backtesting do?"):
    if is_beginner():
        st.markdown("""
        **Backtesting** simulates how your chosen investment mix would have performed in the past.

        - **Growth Curve** \u2014 how your starting money would have grown over time.
        - **Drawdown** \u2014 how far below its peak your portfolio fell.
        - **Buy & Hold** \u2014 invest once, never touch it again.
        - **Rebalancing** \u2014 periodically reset to your target mix. This locks in gains and buys more of what's cheaper.

        **Remember:** past results don't guarantee future performance.
        """)
    else:
        st.markdown("""
        **Backtesting** simulates how your chosen allocation would have performed historically.

        - **Equity Curve** \u2014 how your initial investment would have grown over time.
        - **Drawdown** \u2014 how far below its peak your portfolio fell, and for how long.
        - **Buy & Hold** \u2014 invest once, never touch it again.
        - **Rebalancing** \u2014 periodically reset back to your target weights (e.g. quarterly). This locks in gains from winners and buys more of losers.

        **Remember:** past performance does not guarantee future results. Backtests can overfit to historical data.
        """)

if not weights_valid:
    st.stop()

freq_map = {"None (Buy & Hold)": None, "Never (Buy & Hold)": None, "Monthly": "M", "Quarterly": "Q", "Yearly": "Y"}
freq = freq_map[rebalance_freq]

portfolio_rets = build_portfolio_returns(prices, weights)
if freq:
    rebal_rets = rebalanced_portfolio_returns(prices, weights, rebalance_freq=freq)
else:
    rebal_rets = portfolio_rets

benchmark_ticker = [t for t in tickers if t.startswith("^")]
bench_rets = returns[benchmark_ticker[0]] if benchmark_ticker else None

section_title("\U0001f4c8 Equity Curve & Drawdown")
if is_beginner():
    st.caption("Top: your portfolio value over time. Bottom: how far below the peak at each point.")
else:
    st.caption("Top: portfolio value over time starting from your initial investment. Bottom: how far below the peak at each point.")
portfolios_to_plot = {"Buy & Hold": portfolio_rets}
if freq:
    portfolios_to_plot[f"Rebalanced ({rebalance_freq})"] = rebal_rets
if bench_rets is not None:
    portfolios_to_plot[benchmark_ticker[0]] = bench_rets

curves = compare_portfolios(portfolios_to_plot, initial_value=initial_value)

fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                    subplot_titles=("Equity Curve" if not is_beginner() else "Portfolio Value",
                                    "Drawdown"), vertical_spacing=0.08)
colors = chart_colors(len(curves.columns))
for i, col in enumerate(curves.columns):
    fig.add_trace(go.Scatter(x=curves.index, y=curves[col], name=col, mode="lines",
                             line=dict(color=colors[i])), row=1, col=1)
for i, (name, ret) in enumerate(portfolios_to_plot.items()):
    dd = drawdown_series(ret) * 100
    fig.add_trace(go.Scatter(x=dd.index, y=dd, name=f"{name} DD", mode="lines",
                             line=dict(color=colors[i], dash="dot")), row=2, col=1)
fig.update_layout()
fig.update_yaxes(title_text="Value ($)", row=1, col=1)
fig.update_yaxes(title_text="Drawdown %", row=2, col=1)
apply_theme(fig, height=700)
st.plotly_chart(fig, use_container_width=True)

divider()

section_title("\U0001f4cb Metrics Comparison")
if is_beginner():
    st.caption("Side-by-side metrics for each portfolio variant.")
else:
    st.caption("Side-by-side risk/return metrics for each portfolio variant.")
compare_label = "Compare multiple allocations" if not is_beginner() else "Compare different mixes"
show_compare = st.checkbox(compare_label,
                            help="Add Conservative / Balanced / Aggressive presets to compare different strategies.")

if show_compare:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Conservative**")
        conservative = {}
        for t in tickers:
            conservative[t] = st.number_input(f"{t} %", 0, 100, 10 if t != "^GSPC" else 20, key=f"cons_{t}") / 100
    with col2:
        st.markdown("**Balanced**")
        balanced = {}
        for t in tickers:
            balanced[t] = st.number_input(f"{t} %", 0, 100, round(weights.get(t, 0) * 100), key=f"bal_{t}") / 100
    with col3:
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

table = metrics_table(alloc_returns, benchmark_returns=bench_rets, rf=rf)
styled = format_dataframe_styler(table)
st.dataframe(styled, use_container_width=True, height=350)
render_export_section(table, "backtest_metrics.csv", key="backtest_metrics")

with st.expander("\U0001f4c8 Equity Curve Comparison"):
    if is_beginner():
        st.caption("All allocations plotted together to see which mix grew the most.")
    else:
        st.caption("All allocations plotted together so you can see which strategy grew the most.")
    alloc_curves = compare_portfolios(alloc_returns, initial_value=initial_value)
    fig = go.Figure()
    colors = chart_colors(len(alloc_curves.columns))
    for i, col in enumerate(alloc_curves.columns):
        fig.add_trace(go.Scatter(x=alloc_curves.index, y=alloc_curves[col], name=col, mode="lines",
                                 line=dict(color=colors[i])))
    fig.update_layout(yaxis_title="Value ($)", xaxis_title="Date")
    apply_theme(fig, height=600)
    st.plotly_chart(fig, use_container_width=True)

with st.expander("\U0001f525 Yearly Returns Heatmap"):
    if is_beginner():
        st.caption("Returns for each year. Green = profitable, Red = losing.")
    else:
        st.caption("Annual returns for each strategy. Green = profitable year, Red = losing year.")
    yearly = {}
    for name, ret in alloc_returns.items():
        yearly[name] = ret.groupby(ret.index.year).apply(lambda x: (1 + x).prod() - 1)
    yearly_df = pd.DataFrame(yearly)

    from src.charts import make_heatmap
    fig = make_heatmap(
         z=(yearly_df.values * 100).round(1),
         x=yearly_df.columns.tolist(),
         y=yearly_df.index.tolist(),
         colorscale="RdYlGn",
         zmin=-30, zmax=50,
         height=max(400, len(yearly_df) * 40 + 200),
     )
    st.plotly_chart(fig, use_container_width=True)

divider()
render_next_button("Simulate", "5_Simulate.py")
