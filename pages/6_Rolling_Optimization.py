import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rolling import (
    rolling_optimize, walk_forward_test_returns,
    rolling_weights_over_time, compare_rolling_strategies,
)
from src.portfolio import build_portfolio_returns, equity_curve
from src.metrics import metrics_table, sharpe_ratio, annualized_return
from src.optimization import OPTIMIZATION_TARGETS
from src.ui import (
    init_shared_state, require_data, render_workflow_stepper,
    render_portfolio_info, save_recommended_weights, render_recommended_portfolio,
)

st.set_page_config(page_title="Rolling Optimization", layout="wide")
init_shared_state()
render_workflow_stepper(6)

st.title("Rolling / Walk-Forward Optimization")
require_data()

prices = st.session_state["prices"]
returns = st.session_state["returns"]
tickers = st.session_state.get("tickers", [])
rf = st.session_state.get("risk_free_rate", 0.04)

with st.sidebar:
    render_portfolio_info()
    st.markdown("---")
    st.header("Settings")
    target = st.selectbox("Optimization target", OPTIMIZATION_TARGETS + ["hrp"],
                           help="The strategy to use in each rolling window.")
    train_window = st.selectbox("Training window (days)", [126, 252, 504, 756], index=1,
                                 help="How much historical data to use for optimization. 252 = ~1 year.")
    test_window = st.selectbox("Test window (days)", [5, 21, 42, 63], index=1,
                                help="How far forward to test the optimized weights. 21 = ~1 month.")
    step = st.selectbox("Rebalance step (days)", [5, 21, 42, 63], index=1,
                         help="How often to re-optimize. 21 = monthly rebalance.")

    run_btn = st.button("Run Rolling Optimization", type="primary", use_container_width=True)

    st.markdown("---")
    st.header("Multi-Strategy Comparison")
    compare_targets = st.multiselect(
        "Targets to compare",
        OPTIMIZATION_TARGETS + ["hrp"],
        default=["max_sharpe", "min_volatility", "hrp"],
        help="Run multiple strategies and compare their walk-forward performance side by side."
    )
    run_compare_btn = st.button("Compare Strategies", use_container_width=True)

with st.expander("What is rolling optimization?"):
    st.markdown("""
    **Rolling (walk-forward) optimization** tests how your strategy would perform in real-time by repeatedly:

    1. **Training** — optimizing weights on a past window (e.g. the last 252 trading days)
    2. **Testing** — applying those weights to the next period (e.g. the next 21 days)
    3. **Rolling forward** — moving the window ahead and repeating

    This simulates what would happen if you re-optimized your portfolio periodically — a more realistic test than a single backtest.

    - **Train Sharpe** — how good the optimization looked on past data (in-sample)
    - **Test Return** — what actually happened in the out-of-sample period
    - **Walk-Forward Curve** — cumulative performance if you had followed this strategy
    - **Weights Over Time** — how the optimizer's allocation changed across market regimes
    """)

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
            st.metric("Avg Train Sharpe", f"{results['train_sharpe'].mean():.3f}",
                       help="Average in-sample Sharpe ratio. If much higher than test return, the strategy may be overfitting.")
        with col2:
            st.metric("Avg Test Return", f"{results['test_return'].mean():.2%}",
                       help="Average out-of-sample return per test window.")
        with col3:
            st.metric("Test Win Rate", f"{(results['test_return'] > 0).mean():.1%}",
                       help="% of test periods that were profitable.")

        st.subheader("Weights Over Time")
        st.caption("How the optimizer's allocation changed over time. Large swings suggest the strategy is sensitive to the data window.")
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
            template="plotly_dark", height=500,
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Train vs Test Performance"):
            st.caption("Top: in-sample Sharpe (how good it looked). Bottom: out-of-sample return (what actually happened). "
                       "Big gaps between the two suggest overfitting.")
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                subplot_titles=("Train Sharpe (In-Sample)", "Test Return (Out-of-Sample)"),
                                vertical_spacing=0.08)
            fig.add_trace(go.Bar(
                x=results["date"], y=results["train_sharpe"], name="Train Sharpe",
                marker_color="#4c78a8", opacity=0.7,
            ), row=1, col=1)
            fig.add_trace(go.Bar(
                x=results["date"], y=results["test_return"] * 100, name="Test Return %",
                marker_color=["#00d4aa" if r > 0 else "#e45756" for r in results["test_return"]],
                opacity=0.7,
            ), row=2, col=1)
            fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
            fig.update_layout(
                title=f"Rolling Performance ({target_name}, train: {train_window}d, test: {test_window}d)",
                template="plotly_dark", height=700,
            )
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("Walk-Forward Equity Curve"):
            st.caption("Cumulative performance if you followed the rolling strategy vs a static equal-weight benchmark.")
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
                fig.update_layout(title="Walk-Forward vs Equal Weight", template="plotly_dark", height=500)
                st.plotly_chart(fig, use_container_width=True)

                comp = {f"Walk-Forward ({target_name})": aligned_wf, "Equal Weight": aligned_equal}
                table = metrics_table(comp, rf=rf)
                st.dataframe(table.style.format("{:.4f}"), use_container_width=True)
            else:
                st.info("Not enough data for walk-forward analysis.")
    else:
        st.info("Configure settings in the sidebar and click **Run Rolling Optimization**.")

with tab_compare:
    st.caption("Run multiple optimization strategies in walk-forward mode and compare which one performed best out-of-sample.")
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

            rank_col1, rank_col2 = st.columns(2)
            with rank_col1:
                rank_metric = st.selectbox("Rank strategies by", [
                    "WF Sharpe", "WF Ann. Return (%)", "WF Total Return (%)",
                    "Avg Test Return (%)", "Test Win Rate (%)", "Avg Train Sharpe",
                ], index=0, key="rolling_rank_metric",
                    help="Pick which metric defines 'best'. Higher is always better for these metrics.")
            with rank_col2:
                st.info("Higher is better for all ranking metrics")

            ranked = summary_df.loc[rank_metric].sort_values(ascending=False)
            best_name = ranked.index[0]
            best_val = ranked.iloc[0]

            if best_name and best_name in all_rolling:
                best_res = all_rolling[best_name]
                if len(best_res) > 0:
                    latest_weights = best_res.iloc[-1]["weights"]
                    save_recommended_weights(
                        latest_weights,
                        f"Rolling: {best_name} ({rank_metric}={best_val:.3f})"
                    )

            st.subheader("Best Strategy")
            st.success(f"**{best_name}** — {rank_metric}: {best_val:.3f}")
            st.caption("This strategy's latest optimized weights have been saved as the recommended portfolio.")

            st.markdown("**Ranking:**")
            for i, (name, val) in enumerate(ranked.items()):
                medal = {0: " :1st_place_medal:", 1: " :2nd_place_medal:", 2: " :3rd_place_medal:"}.get(i, "")
                st.markdown(f"{i+1}. **{name}** — {rank_metric}: `{val:.3f}`{medal}")

            st.markdown("---")
            st.subheader("All Strategies")
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
                template="plotly_dark", height=500,
            )
            st.plotly_chart(fig, use_container_width=True)

            if best_name and len(all_rolling[best_name]) > 0:
                with st.expander(f"Weights Over Time — {best_name} (Best)"):
                    best_weights_df = rolling_weights_over_time(all_rolling[best_name])
                    fig = go.Figure()
                    for col in best_weights_df.columns:
                        fig.add_trace(go.Scatter(
                            x=best_weights_df.index, y=best_weights_df[col] * 100,
                            name=col, mode="lines", stackgroup="one",
                        ))
                    fig.update_layout(
                        title=f"Rolling Weights ({best_name})",
                        yaxis_title="Weight %", xaxis_title="Date",
                        template="plotly_dark", height=500,
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Select at least one target and click **Compare Strategies**.")
    else:
        st.info("Select targets in the sidebar and click **Compare Strategies**.")

st.markdown("---")
render_recommended_portfolio(prices, returns, tickers, rf)
