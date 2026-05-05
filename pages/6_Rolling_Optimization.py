import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.rolling import (
    rolling_optimize, walk_forward_test_returns,
    rolling_weights_over_time, compare_rolling_strategies,
)
from src.portfolio import build_portfolio_returns, equity_curve
from src.metrics import metrics_table, sharpe_ratio, annualized_return
from src.optimization import OPTIMIZATION_TARGETS

st.set_page_config(page_title="Rolling Optimization", layout="wide")
st.title("Rolling / Walk-Forward Optimization")

if "returns" not in st.session_state:
    st.warning("Go to **Overview** first to fetch data.")
    st.stop()

prices = st.session_state["prices"]
returns = st.session_state["returns"]
tickers = st.session_state.get("tickers", [])

with st.sidebar:
    st.header("Settings")
    target = st.selectbox("Optimization target", OPTIMIZATION_TARGETS + ["hrp"])
    train_window = st.selectbox("Training window (days)", [126, 252, 504, 756], index=1)
    test_window = st.selectbox("Test window (days)", [5, 21, 42, 63], index=1)
    step = st.selectbox("Rebalance step (days)", [5, 21, 42, 63], index=1)
    rf = st.number_input("Risk-free rate (%)", value=4.0, min_value=0.0, max_value=20.0, step=0.5) / 100

    run_btn = st.button("Run Rolling Optimization", type="primary", use_container_width=True)

    st.markdown("---")
    st.header("Multi-Strategy Comparison")
    compare_targets = st.multiselect(
        "Select targets to compare",
        OPTIMIZATION_TARGETS + ["hrp"],
        default=["max_sharpe", "min_volatility", "hrp"],
    )
    run_compare_btn = st.button("Compare Strategies", use_container_width=True)

tab_single, tab_compare = st.tabs(["Single Target", "Multi-Strategy Comparison"])

with tab_single:
    if run_btn or "rolling_results" in st.session_state:
        if run_btn:
            with st.spinner(f"Running rolling optimization ({target})..."):
                results = rolling_optimize(
                    prices, target=target, train_window=train_window,
                    test_window=test_window, step=step, risk_free_rate=rf,
                )
                st.session_state["rolling_results"] = results
                st.session_state["rolling_target"] = target

        results = st.session_state["rolling_results"]
        target_name = st.session_state.get("rolling_target", target)

        st.subheader(f"Results: {target_name} ({len(results)} windows)")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Avg Train Sharpe", f"{results['train_sharpe'].mean():.3f}")
        with col2:
            st.metric("Avg Test Return", f"{results['test_return'].mean():.2%}")
        with col3:
            st.metric("Test Win Rate", f"{(results['test_return'] > 0).mean():.1%}")

        st.subheader("Weights Over Time")
        weights_df = rolling_weights_over_time(results)
        fig = go.Figure()
        for col in weights_df.columns:
            fig.add_trace(go.Scatter(
                x=weights_df.index, y=weights_df[col] * 100,
                name=col, mode="lines", stackgroup="one",
            ))
        fig.update_layout(
            title=f"Rolling Weights ({target_name})",
            yaxis_title="Weight %", xaxis_title="Date",
            template="plotly_white", height=500,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Train vs Test Performance")
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            subplot_titles=("Train Sharpe (In-Sample)", "Test Return (Out-of-Sample)"),
                            vertical_spacing=0.08)
        fig.add_trace(go.Bar(
            x=results["date"], y=results["train_sharpe"], name="Train Sharpe",
            marker_color="blue", opacity=0.7,
        ), row=1, col=1)
        fig.add_trace(go.Bar(
            x=results["date"], y=results["test_return"] * 100, name="Test Return %",
            marker_color=["green" if r > 0 else "red" for r in results["test_return"]],
            opacity=0.7,
        ), row=2, col=1)
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
        fig.update_layout(
            title=f"Rolling Performance ({target_name}, train: {train_window}d, test: {test_window}d)",
            template="plotly_white", height=700,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Walk-Forward Equity Curve")
        wf_returns = walk_forward_test_returns(results, prices)
        if len(wf_returns) > 0:
            equal_w = {t: 1.0 / len(tickers) for t in tickers}
            equal_ret = build_portfolio_returns(prices, equal_w)
            aligned_equal = equal_ret.reindex(wf_returns.index).dropna()
            aligned_wf = wf_returns.reindex(aligned_equal.index).dropna()

            curves = pd.DataFrame({
                f"Walk-Forward ({target_name})": equity_curve(aligned_wf, 10000),
                "Equal Weight": equity_curve(aligned_equal, 10000),
            })
            fig = go.Figure()
            for col in curves.columns:
                fig.add_trace(go.Scatter(x=curves.index, y=curves[col], name=col, mode="lines"))
            fig.update_layout(title="Walk-Forward vs Equal Weight", template="plotly_white", height=500)
            st.plotly_chart(fig, use_container_width=True)

            comp = {f"Walk-Forward ({target_name})": aligned_wf, "Equal Weight": aligned_equal}
            table = metrics_table(comp)
            st.dataframe(table.style.format("{:.4f}"), use_container_width=True)
        else:
            st.info("Not enough data for walk-forward analysis.")
    else:
        st.info("Configure settings in the sidebar and click **Run Rolling Optimization**.")

with tab_compare:
    if run_compare_btn or "compare_results" in st.session_state:
        if run_compare_btn and compare_targets:
            with st.spinner(f"Comparing {len(compare_targets)} strategies..."):
                all_rolling = compare_rolling_strategies(
                    prices, targets=compare_targets, train_window=train_window,
                    test_window=test_window, step=step, risk_free_rate=rf,
                )
                st.session_state["compare_results"] = all_rolling

        if "compare_results" in st.session_state:
            all_rolling = st.session_state["compare_results"]

            summary = {}
            for name, res in all_rolling.items():
                wf_ret = walk_forward_test_returns(res, prices)
                entry = {
                    "Avg Train Sharpe": res["train_sharpe"].mean(),
                    "Avg Test Return (%)": res["test_return"].mean() * 100,
                    "Test Win Rate (%)": (res["test_return"] > 0).mean() * 100,
                    "N Periods": len(res),
                }
                if len(wf_ret) > 0:
                    entry["WF Total Return (%)"] = ((1 + wf_ret).prod() - 1) * 100
                    entry["WF Sharpe"] = sharpe_ratio(wf_ret)
                    entry["WF Ann. Return (%)"] = annualized_return(wf_ret) * 100
                summary[name] = entry

            summary_df = pd.DataFrame(summary)
            st.dataframe(summary_df.style.format("{:.3f}"), use_container_width=True)

            metrics_to_plot = ["Avg Train Sharpe", "Avg Test Return (%)", "Test Win Rate (%)"]
            fig = go.Figure()
            for metric in metrics_to_plot:
                fig.add_trace(go.Bar(
                    x=list(summary.keys()),
                    y=[summary[k][metric] for k in summary],
                    name=metric,
                ))
            fig.update_layout(
                title="Rolling Strategy Comparison", barmode="group",
                template="plotly_white", height=500,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Select at least one target and click **Compare Strategies**.")
    else:
        st.info("Select targets in the sidebar and click **Compare Strategies**.")
