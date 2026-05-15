import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.metrics import (
    metrics_table, sharpe_ratio, sortino_ratio,
    calmar_ratio, omega_ratio, annualized_return, annualized_volatility,
    quantstats_report,
)
from src.ui import (
    init_shared_state, require_data, render_workflow_stepper,
    render_next_button, render_portfolio_info, render_page_header,
    is_beginner, label,
)
from src.styles import inject_global_styles, divider, section_title
from src.charts import apply_theme, chart_colors, make_scatter_plot, format_dataframe_styler
from src.export import render_export_section

st.set_page_config(page_title="Risk Metrics", layout="wide")
inject_global_styles()
init_shared_state()
render_workflow_stepper(2)
render_page_header("Risk")
require_data()

prices = st.session_state["prices"]
returns = st.session_state["returns"]
tickers = st.session_state.get("tickers", [])
rf = st.session_state.get("risk_free_rate", 0.04)

with st.sidebar:
    render_portfolio_info()
    st.markdown("---")
    st.header("Settings")
    bench_label = "Benchmark" if not is_beginner() else "Compare Against"
    bench_help = (
        "Select a benchmark to compute relative metrics like Alpha, Beta, Treynor Ratio, and Information Ratio against."
        if not is_beginner()
        else "Pick an investment to compare against."
    )
    benchmark_options = ["None"] + tickers
    benchmark_choice = st.selectbox(bench_label, benchmark_options, index=0, help=bench_help)

benchmark = None
if benchmark_choice != "None":
    benchmark = returns[benchmark_choice]

assets_to_analyze = [t for t in tickers if t != benchmark_choice]
if not assets_to_analyze:
    assets_to_analyze = tickers


def _compute_rolling(window_returns: pd.Series, metric: str, rf: float) -> float:
    try:
        r = window_returns
        if len(r) < 10:
            return np.nan
        ann_ret = (1 + r).prod() ** (252 / len(r)) - 1
        ann_vol = r.std() * np.sqrt(252)
        if metric == "Sharpe Ratio":
            return (ann_ret - rf) / ann_vol if ann_vol != 0 else 0.0
        elif metric == "Sortino Ratio":
            threshold = rf / 252
            downside_diff = np.minimum(r - threshold, 0.0)
            downside_dev = np.sqrt((downside_diff ** 2).mean()) * np.sqrt(252)
            return (ann_ret - rf) / downside_dev if downside_dev != 0 else float("inf")
        elif metric == "Calmar Ratio":
            cum = (1 + r).cumprod()
            mdd = ((cum - cum.cummax()) / cum.cummax()).min()
            return (ann_ret - rf) / abs(mdd) if mdd != 0 else 0.0
        elif metric == "Omega Ratio":
            threshold = rf / 252
            gains = (r[r > threshold] - threshold).sum()
            losses = (threshold - r[r < threshold]).sum()
            return gains / losses if losses != 0 else float("inf")
        elif metric == "Volatility":
            return ann_vol
        elif metric == "Max Drawdown":
            cum = (1 + r).cumprod()
            return ((cum - cum.cummax()) / cum.cummax()).min()
        elif metric == "CVaR (95%)":
            var_threshold = np.percentile(r, 5)
            tail = r[r <= var_threshold]
            return tail.mean() if len(tail) > 0 else var_threshold
        elif metric == "CAGR":
            return (1 + r).prod() ** (252 / len(r)) - 1
        elif metric == "Annualized Return":
            return ann_ret
        elif metric == "Skewness":
            return float(r.skew())
        elif metric == "Kurtosis":
            return float(r.kurtosis())
        return np.nan
    except Exception:
        return np.nan


section_title("\U0001f4ca Full Metrics Table")
with st.expander("\u2753 What do these metrics mean?" if not is_beginner() else "\u2753 What do these numbers mean?", expanded=False):
    if is_beginner():
        st.markdown("""
        | Metric | What it tells you |
        |--------|-------------------|
        | **Avg Yearly Growth** | Your average yearly return if you reinvest all profits. |
        | **Yearly Return** | Simple annualized return over the period. |
        | **Price Swings** | How much the price bounces around. Higher = more unpredictable. |
        | **Risk-Adjusted Score** | How much return you get for the risk you take. Above 1.0 is good. |
        | **Downside Score** | Like the above but only counts bad days. Better for crypto. |
        | **Return vs Worst Loss** | Is the return worth the worst drop you had to endure? |
        | **Win/Loss Ratio** | Probability of gains vs losses. Above 1.0 is good. |
        | **Worst Loss** | Biggest drop from peak. -30% = you lost 30% from your highest point. |
        | **Bad-Day Loss** | How bad it gets on the worst 5% of days. |
        | **Gain/Loss Balance** | Negative = more big losses. Positive = more big gains. |
        | **Extreme Events** | High = more extreme events than normal (crashes & rallies). |
        """)
    else:
        st.markdown("""
        | Metric | What it tells you |
        |--------|-------------------|
        | **CAGR** | Compound Annual Growth Rate — your average yearly return if profits were reinvested. |
        | **Annualized Return** | Simple annualized return over the period. |
        | **Annualized Volatility** | How much the returns swing up and down (annualized std dev). Higher = riskier. |
        | **Sharpe Ratio** | Return per unit of risk. (Return - Risk-free rate) / Volatility. >1 is good, >2 is excellent. |
        | **Sortino Ratio** | Like Sharpe but only penalizes downside volatility. Better for asymmetric returns. |
        | **Calmar Ratio** | Return vs. max drawdown. High = good return for the worst loss you endured. |
        | **Omega Ratio** | Probability-weighted gains vs losses above/below a threshold. >1 is good. |
        | **Max Drawdown** | Worst peak-to-trough decline. -30% means you lost 30% from your portfolio's all-time high. |
        | **CVaR (95%)** | Expected loss in the worst 5% of days. More sensitive to tail risk than VaR. |
        | **Skewness** | Negative = more big losses than gains. Positive = more big gains. |
        | **Kurtosis** | High = fat tails (more extreme events than a normal bell curve predicts). |
        | **Beta** | How much the asset moves with the benchmark. >1 = more volatile than benchmark. |
        | **Treynor Ratio** | Like Sharpe but uses Beta instead of volatility. Better for diversified portfolios. |
        | **Information Ratio** | Excess return vs benchmark per unit of tracking error. >0.5 is good. |
        | **Alpha** | Return above what the CAPM model predicts. Positive = the asset outperformed expectations. |
        | **Best/Worst Day** | Single best and worst daily returns. |
        | **Avg Daily Return** | Mean of daily returns. |
        """)

asset_returns = {t: returns[t] for t in assets_to_analyze}
table = metrics_table(asset_returns, benchmark_returns=benchmark, rf=rf)

renamed_table = table.copy()
if is_beginner():
    rename_map = {}
    for col in renamed_table.columns:
        new_col = label(col)
        if new_col != col:
            rename_map[col] = new_col
    if rename_map:
        renamed_table = renamed_table.rename(columns=rename_map)

styled = format_dataframe_styler(renamed_table)
st.dataframe(styled, use_container_width=True, height=400)
render_export_section(table, "risk_metrics.csv", key="risk_metrics")

divider()

col_scatter, col_ratios = st.columns(2)

with col_scatter:
    section_title("\U0001f4c8 Risk vs Return")
    if is_beginner():
        st.caption("Each dot is an investment. Top-left is ideal: high return with low volatility.")
    else:
        st.caption("Each dot is an asset. Top-left is the sweet spot: high return with low volatility.")
    points = []
    for t in assets_to_analyze:
        points.append({
            "x": annualized_volatility(returns[t]),
            "y": annualized_return(returns[t]),
            "name": t,
            "size": 12,
        })
    if benchmark is not None:
        points.append({
            "x": annualized_volatility(benchmark),
            "y": annualized_return(benchmark),
            "name": benchmark_choice,
            "size": 14,
            "symbol": "star",
        })
    fig = make_scatter_plot(points, x_title="Annualized Volatility", y_title="Annualized Return", height=450)
    st.plotly_chart(fig, use_container_width=True)

with col_ratios:
    section_title("\U0001f4ca Risk-Adjusted Ratios")
    if is_beginner():
        st.caption("Taller bars = better return for the risk taken.")
    else:
        st.caption("Higher bars = better risk-adjusted performance.")
    ratios_data = {}
    for t in assets_to_analyze:
        r = returns[t]
        ratios_data[t] = {
            label("Sharpe"): sharpe_ratio(r, rf=rf),
            label("Sortino"): sortino_ratio(r, rf=rf),
            label("Calmar"): calmar_ratio(r, rf=rf),
            label("Omega"): omega_ratio(r),
        }
    ratios_df = pd.DataFrame(ratios_data)

    from src.charts import make_bar_chart
    fig = make_bar_chart(
        categories=list(ratios_df.columns),
        values_dict={idx: ratios_df.loc[idx].tolist() for idx in ratios_df.index},
        y_title="Ratio Value",
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

divider()

with st.expander("\U0001f4c8 Rolling Metrics"):
    if is_beginner():
        st.caption("See how a metric changes over time. Useful to check if an investment is getting more or less risky.")
    else:
        st.caption("How a metric changes over time. Useful to see if risk is stable or varies across market regimes.")
    col_w, col_m = st.columns(2)
    with col_w:
        window = st.selectbox("Rolling window", [63, 126, 252, 504], index=2,
                               help="Number of trading days in each rolling calculation. 252 = ~1 year.")
    with col_m:
        rolling_metrics = [
            "Sharpe Ratio", "Sortino Ratio", "Calmar Ratio", "Omega Ratio",
            "Volatility", "Max Drawdown", "CVaR (95%)", "CAGR",
            "Annualized Return", "Skewness", "Kurtosis",
        ]
        display_metrics = [label(m) for m in rolling_metrics]
        metric_idx = st.selectbox("Rolling metric", range(len(rolling_metrics)),
                                  format_func=lambda i: display_metrics[i])
        metric_choice = rolling_metrics[metric_idx]

    fig = go.Figure()
    colors = chart_colors(len(assets_to_analyze))
    for i, t in enumerate(assets_to_analyze):
        r = returns[t]
        rolling_metric = r.rolling(window).apply(
            lambda x: _compute_rolling(x, metric_choice, rf), raw=False,
        )
        fig.add_trace(go.Scatter(x=rolling_metric.index, y=rolling_metric, name=t, mode="lines",
                                 line=dict(color=colors[i])))
    fig.update_layout(yaxis_title=metric_choice, xaxis_title="Date")
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    apply_theme(fig, height=500)
    st.plotly_chart(fig, use_container_width=True)

with st.expander("\U0001f4c9 Drawdowns"):
    if is_beginner():
        st.caption("How far below its peak each investment has fallen. Deeper/longer drops = harder to hold through.")
    else:
        st.caption("How far below its peak each asset has fallen. Deeper/longer drawdowns = more pain to hold through.")
    fig = go.Figure()
    colors = chart_colors(len(assets_to_analyze))
    for i, t in enumerate(assets_to_analyze):
        cum = (1 + returns[t]).cumprod()
        running_max = cum.cummax()
        dd = (cum - running_max) / running_max * 100
        fig.add_trace(go.Scatter(x=dd.index, y=dd, name=t, mode="lines", fill="tozeroy",
                                 line=dict(color=colors[i])))
    fig.update_layout(yaxis_title="Drawdown %", xaxis_title="Date")
    apply_theme(fig, height=500)
    st.plotly_chart(fig, use_container_width=True)

with st.expander("\U0001f4e1 Generate QuantStats Report"):
    st.caption("Generate a detailed HTML report for a single asset using QuantStats.")
    report_ticker = st.selectbox("Asset", tickers, key="qs_report_ticker")
    report_benchmark = st.text_input("Benchmark ticker", value="SPY", key="qs_report_bench")
    if st.button("Generate Report", type="primary"):
        import tempfile
        import shutil
        with st.spinner("Generating QuantStats report..."):
            try:
                tmpdir = tempfile.mkdtemp()
                outpath = quantstats_report(
                    returns[report_ticker], benchmark=report_benchmark,
                    title=f"{report_ticker} Analysis", output_dir=tmpdir,
                )
                if os.path.exists(outpath):
                    with open(outpath, "rb") as f:
                        st.download_button("Download HTML Report", f,
                                           file_name=f"{report_ticker}_report.html",
                                           mime="text/html")
                    shutil.rmtree(tmpdir, ignore_errors=True)
                else:
                    st.error("Report file not found. Check that quantstats is installed correctly.")
            except Exception as e:
                st.error(f"Failed to generate report: {e}")

divider()
render_next_button("Optimize", "3_Optimize.py")
