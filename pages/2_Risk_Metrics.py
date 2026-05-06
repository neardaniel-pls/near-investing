import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.metrics import (
    compute_all_metrics, metrics_table, sharpe_ratio, sortino_ratio,
    calmar_ratio, omega_ratio, annualized_return, annualized_volatility,
    max_drawdown, cvar, cagr, quantstats_report,
)
from src.ui import (
    init_shared_state, require_data, render_workflow_stepper,
    render_next_button, render_portfolio_info,
)

st.set_page_config(page_title="Risk Metrics", layout="wide")
init_shared_state()
render_workflow_stepper(2)

st.title("Risk Metrics")
require_data()

prices = st.session_state["prices"]
returns = st.session_state["returns"]
tickers = st.session_state.get("tickers", [])
rf = st.session_state.get("risk_free_rate", 0.04)

with st.sidebar:
    render_portfolio_info()
    st.markdown("---")
    st.header("Settings")
    benchmark_options = ["None"] + tickers
    benchmark_choice = st.selectbox(
        "Benchmark", benchmark_options, index=0,
        help="Select a benchmark to compute relative metrics like Alpha, Beta, Treynor Ratio, and Information Ratio against."
    )

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


st.subheader("Full Metrics Table")
with st.expander("What do these metrics mean?", expanded=False):
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
st.dataframe(table.style.format("{:.4f}"), use_container_width=True, height=400)
csv = table.to_csv()
st.download_button("Download Metrics CSV", csv, "risk_metrics.csv", "text/csv")

st.markdown("---")

col_scatter, col_ratios = st.columns(2)

with col_scatter:
    st.subheader("Risk vs Return")
    st.caption("Each dot is an asset. Top-left is the sweet spot: high return with low volatility.")
    fig = go.Figure()
    for t in assets_to_analyze:
        fig.add_trace(go.Scatter(
            x=[annualized_volatility(returns[t])],
            y=[annualized_return(returns[t])],
            mode="markers+text", name=t, text=[t],
            textposition="top center", marker=dict(size=12),
        ))
    if benchmark is not None:
        fig.add_trace(go.Scatter(
            x=[annualized_volatility(benchmark)],
            y=[annualized_return(benchmark)],
            mode="markers+text", name=benchmark_choice, text=[benchmark_choice],
            textposition="top center", marker=dict(size=14, symbol="star"),
        ))
    fig.update_layout(
        xaxis_title="Annualized Volatility", yaxis_title="Annualized Return",
        template="plotly_dark", height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

with col_ratios:
    st.subheader("Risk-Adjusted Ratios")
    st.caption("Higher bars = better risk-adjusted performance. Compare assets on equal footing.")
    ratios_data = {}
    for t in assets_to_analyze:
        r = returns[t]
        ratios_data[t] = {
            "Sharpe": sharpe_ratio(r, rf=rf),
            "Sortino": sortino_ratio(r, rf=rf),
            "Calmar": calmar_ratio(r, rf=rf),
            "Omega": omega_ratio(r),
        }
    ratios_df = pd.DataFrame(ratios_data)

    fig = go.Figure()
    for ratio_name in ratios_df.index:
        fig.add_trace(go.Bar(x=ratios_df.columns, y=ratios_df.loc[ratio_name], name=ratio_name))
    fig.update_layout(
        yaxis_title="Ratio Value", barmode="group", template="plotly_dark", height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

with st.expander("Rolling Metrics"):
    st.caption("How a metric changes over time. Useful to see if risk is stable or varies across market regimes.")
    col_w, col_m = st.columns(2)
    with col_w:
        window = st.selectbox("Rolling window", [63, 126, 252, 504], index=2,
                               help="Number of trading days in each rolling calculation. 252 = ~1 year.")
    with col_m:
        metric_choice = st.selectbox("Rolling metric", [
            "Sharpe Ratio", "Sortino Ratio", "Calmar Ratio", "Omega Ratio",
            "Volatility", "Max Drawdown", "CVaR (95%)", "CAGR",
            "Annualized Return", "Skewness", "Kurtosis",
        ])

    fig = go.Figure()
    for t in assets_to_analyze:
        r = returns[t]
        rolling_metric = r.rolling(window).apply(
            lambda x: _compute_rolling(x, metric_choice, rf), raw=False,
        )
        fig.add_trace(go.Scatter(x=rolling_metric.index, y=rolling_metric, name=t, mode="lines"))
    fig.update_layout(
        title=f"Rolling {metric_choice} ({window}-day window)",
        yaxis_title=metric_choice, xaxis_title="Date",
        template="plotly_dark", height=500,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    st.plotly_chart(fig, use_container_width=True)

with st.expander("Drawdowns"):
    st.caption("How far below its peak each asset has fallen. Deeper/longer drawdowns = more pain to hold through.")
    fig = go.Figure()
    for t in assets_to_analyze:
        cum = (1 + returns[t]).cumprod()
        running_max = cum.cummax()
        dd = (cum - running_max) / running_max * 100
        fig.add_trace(go.Scatter(x=dd.index, y=dd, name=t, mode="lines", fill="tozeroy"))
    fig.update_layout(
        title="Drawdown (%)", yaxis_title="Drawdown %", xaxis_title="Date",
        template="plotly_dark", height=500,
    )
    st.plotly_chart(fig, use_container_width=True)

with st.expander("Generate QuantStats Report"):
    st.caption("Generate a detailed HTML report for a single asset using QuantStats. "
               "Includes rolling metrics, drawdowns, monthly returns, and more.")
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

st.markdown("---")
render_next_button("Backtest", "3_Backtest.py")
