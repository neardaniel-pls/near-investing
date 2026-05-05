import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.metrics import (
    compute_all_metrics, metrics_table, sharpe_ratio, sortino_ratio,
    calmar_ratio, omega_ratio, annualized_return, annualized_volatility,
    max_drawdown, cvar, cagr, RISK_FREE_RATE,
)

st.set_page_config(page_title="Risk Metrics", layout="wide")
st.title("Risk Metrics")


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
            downside = r[r < 0]
            ds_vol = downside.std() * np.sqrt(252) if len(downside) > 0 else 1e-10
            return (ann_ret - rf) / ds_vol
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

if "returns" not in st.session_state:
    st.warning("Go to **Overview** first to fetch data.")
    st.stop()

prices = st.session_state["prices"]
returns = st.session_state["returns"]
tickers = st.session_state.get("tickers", [])

with st.sidebar:
    st.header("Settings")
    rf_rate = st.number_input("Risk-free rate (%)", value=4.0, min_value=0.0, max_value=20.0, step=0.5) / 100
    benchmark_options = ["None"] + tickers
    benchmark_choice = st.selectbox("Benchmark", benchmark_options, index=0)

benchmark = None
if benchmark_choice != "None":
    benchmark = returns[benchmark_choice]

assets_to_analyze = [t for t in tickers if t != benchmark_choice]
if not assets_to_analyze:
    assets_to_analyze = tickers

tab_table, tab_scatter, tab_rolling, tab_drawdown, tab_ratios = st.tabs(
    ["Metrics Table", "Risk vs Return", "Rolling Metrics", "Drawdowns", "Ratios Chart"]
)

with tab_table:
    st.subheader("Full Risk/Return Metrics")
    asset_returns = {t: returns[t] for t in assets_to_analyze}
    table = metrics_table(asset_returns, benchmark_returns=benchmark)
    st.dataframe(table.style.format("{:.4f}"), use_container_width=True, height=600)

with tab_scatter:
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
        title="Risk vs Return (Annualized)",
        xaxis_title="Annualized Volatility", yaxis_title="Annualized Return",
        template="plotly_white", height=600,
    )
    st.plotly_chart(fig, use_container_width=True)

with tab_rolling:
    window = st.selectbox("Rolling window", [63, 126, 252, 504], index=2)
    metric_choice = st.selectbox("Rolling metric", [
        "Sharpe Ratio", "Sortino Ratio", "Calmar Ratio", "Omega Ratio",
        "Volatility", "Max Drawdown", "CVaR (95%)", "CAGR",
        "Annualized Return", "Skewness", "Kurtosis",
    ])

    fig = go.Figure()
    for t in assets_to_analyze:
        r = returns[t]
        rolling_metric = r.rolling(window).apply(
            lambda x: _compute_rolling(x, metric_choice, rf_rate), raw=False,
        )
        fig.add_trace(go.Scatter(x=rolling_metric.index, y=rolling_metric, name=t, mode="lines"))

    fig.update_layout(
        title=f"Rolling {metric_choice} ({window}-day window)",
        yaxis_title=metric_choice, xaxis_title="Date",
        template="plotly_white", height=500,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    st.plotly_chart(fig, use_container_width=True)

with tab_drawdown:
    fig = go.Figure()
    for t in assets_to_analyze:
        cum = (1 + returns[t]).cumprod()
        running_max = cum.cummax()
        dd = (cum - running_max) / running_max * 100
        fig.add_trace(go.Scatter(x=dd.index, y=dd, name=t, mode="lines", fill="tozeroy"))
    fig.update_layout(
        title="Drawdown (%)", yaxis_title="Drawdown %", xaxis_title="Date",
        template="plotly_white", height=500,
    )
    st.plotly_chart(fig, use_container_width=True)

with tab_ratios:
    ratios_data = {}
    for t in assets_to_analyze:
        r = returns[t]
        ratios_data[t] = {
            "Sharpe": sharpe_ratio(r, rf=rf_rate),
            "Sortino": sortino_ratio(r, rf=rf_rate),
            "Calmar": calmar_ratio(r, rf=rf_rate),
            "Omega": omega_ratio(r),
        }
    ratios_df = pd.DataFrame(ratios_data)

    fig = go.Figure()
    for ratio_name in ratios_df.index:
        fig.add_trace(go.Bar(x=ratios_df.columns, y=ratios_df.loc[ratio_name], name=ratio_name))
    fig.update_layout(
        title="Risk-Adjusted Return Ratios", yaxis_title="Ratio Value",
        barmode="group", template="plotly_white", height=500,
    )
    st.plotly_chart(fig, use_container_width=True)
