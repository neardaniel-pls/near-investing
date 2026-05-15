import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.optimization import (
    optimize_portfolio, optimize_all_strategies,
    black_litterman_optimize, kelly_criterion,
    efficient_frontier_data, compute_expected_returns,
    OPTIMIZATION_TARGETS,
)
from src.portfolio import build_portfolio_returns, compare_portfolios
from src.metrics import metrics_table
from src.ui import (
    init_shared_state, require_data, render_workflow_stepper,
    render_next_button, render_portfolio_info, save_recommended_weights,
    render_recommended_portfolio, render_page_header,
    is_beginner, label,
)
from src.styles import inject_global_styles, divider, section_title
from src.charts import apply_theme, chart_colors, make_pie_chart, make_bar_chart, format_dataframe_styler
from src.export import render_export_section

st.set_page_config(page_title="Optimize", layout="wide")
inject_global_styles()
init_shared_state()
render_workflow_stepper(3)
render_page_header("Optimize")
require_data()

prices = st.session_state["prices"]
returns = st.session_state["returns"]
tickers = st.session_state.get("tickers", [])
rf = st.session_state.get("risk_free_rate", 0.04)

TARGET_DESCRIPTIONS = {
    "max_sharpe": "Maximize risk-adjusted return",
    "min_volatility": "Minimize price swings",
    "max_quadratic_utility": "Balance return vs risk based on your tolerance",
    "efficient_return": "Safest way to hit a target return",
    "efficient_risk": "Best return within your risk limit",
    "min_cvar": "Minimize extreme losses (worst 5% of days)",
    "min_semivariance": "Minimize downside risk only",
    "semivariance_utility": "Best return-to-downside-risk trade-off",
    "max_return_min_risk": "Diversified max Sharpe (avoids concentrated bets)",
    "hrp": "Cluster-based diversification (no return estimates needed)",
}

TARGET_BEGINNER = {
    "max_sharpe": "Best return for the risk taken",
    "min_volatility": "Smoothest ride (least price swings)",
    "max_quadratic_utility": "Balanced return and risk",
    "efficient_return": "Safest way to reach a target yearly gain",
    "efficient_risk": "Best return within your comfort zone",
    "min_cvar": "Protect against market crashes",
    "min_semivariance": "Focus only on avoiding losses",
    "semivariance_utility": "Best return vs downside risk",
    "max_return_min_risk": "Best diversified mix",
    "hrp": "Smart diversification without guessing returns",
}

with st.sidebar:
    render_portfolio_info()
    st.markdown("---")

with st.expander("\u2753 What is portfolio optimization?" if not is_beginner() else "\u2753 How does optimization work?"):
    if is_beginner():
        st.markdown("""
        **Portfolio optimization** finds the best mix of investments based on historical data. It uses math to figure out what percentage of your money to put in each asset.

        Each method below has a different idea of what "best" means \u2014 pick the one that matches your goal.

        The **Efficient Frontier** shows the trade-off between risk and return. Anything below the line can be improved.
        """)
    else:
        st.markdown("""
        **Portfolio optimization** uses math to find the asset allocation that best achieves a specific goal (max return, min risk, etc.) based on historical data.

        ### Mean-Variance Methods (Markowitz)
        - **max_sharpe** \u2014 Highest Sharpe ratio (best risk-adjusted return)
        - **min_volatility** \u2014 Lowest possible volatility
        - **max_quadratic_utility** \u2014 Customizable return vs risk trade-off
        - **efficient_return** \u2014 Minimize risk for a target return
        - **efficient_risk** \u2014 Maximize return for a target risk level
        - **max_return_min_risk** \u2014 Regularized Sharpe (more diversified)

        ### Downside Risk Methods
        - **min_cvar** \u2014 Minimize expected loss in worst 5% of days
        - **min_semivariance** \u2014 Minimize downside volatility only
        - **semivariance_utility** \u2014 Quadratic utility under semivariance

        ### Alternative Methods
        - **hrp** \u2014 Hierarchical Risk Parity (cluster-based, no return estimates)
        - **Kelly Criterion** \u2014 Optimal position sizing for max compounding
        - **Black-Litterman** \u2014 Incorporate personal views into market equilibrium
        """)

tab_labels = ["Single Target", "Compare All", "Black-Litterman & Kelly", "Efficient Frontier"]
if is_beginner():
    tab_labels = ["One Strategy", "Compare All", "Custom Views & Sizing", "Risk vs Return Curve"]
tab_single, tab_all, tab_bl, tab_frontier = st.tabs(tab_labels)

with tab_single:
    section_title("Choose Optimization Target")
    col1, col2 = st.columns([1, 2])

    with col1:
        opt_label = "Optimize for" if not is_beginner() else "What do you want?"
        desc_dict = TARGET_BEGINNER if is_beginner() else TARGET_DESCRIPTIONS
        target = st.selectbox(
            opt_label,
            OPTIMIZATION_TARGETS + ["hrp"],
            format_func=lambda x: f"{x} \u2014 {desc_dict.get(x, '')}",
            help="Pick what 'best' means. Different targets suit different goals." if not is_beginner()
            else "Choose your goal. Each strategy optimizes for something different.",
        )
        current_desc = TARGET_BEGINNER.get(target, TARGET_DESCRIPTIONS.get(target, "")) if is_beginner() \
            else TARGET_DESCRIPTIONS.get(target, "")
        st.info(f"**{target}**: {current_desc}")

        target_value = None
        if target == "efficient_return":
            mu = compute_expected_returns(prices)
            ret_label = "Target annual return (%)" if not is_beginner() else "How much yearly gain do you want (%)"
            target_value = st.slider(ret_label,
                                     float(mu.min() * 100), float(mu.max() * 100),
                                     float(mu.mean() * 100), step=0.5) / 100
        elif target == "efficient_risk":
            risk_label = "Target annual volatility (%)" if not is_beginner() else "Max price swings you can handle (%)"
            target_value = st.slider(risk_label, 5.0, 50.0, 20.0, step=0.5) / 100

        opt_btn_label = "Optimize" if not is_beginner() else "Find Best Mix"
        if st.button(opt_btn_label, type="primary"):
            with st.spinner("Optimizing..."):
                if target == "hrp":
                    w = optimize_portfolio(prices, target="hrp")
                else:
                    w = optimize_portfolio(prices, target=target, target_value=target_value, risk_free_rate=rf)
                st.session_state["opt_weights"] = w
                save_recommended_weights(w, f"Single: {target}")
                st.toast(f"Optimization complete: {target}", icon="\u2705")

        if "opt_weights" in st.session_state:
            w = st.session_state["opt_weights"]
            section_title("Optimal Weights")
            for t, weight in sorted(w.items(), key=lambda x: -x[1]):
                if abs(weight) > 0.001:
                    bar_len = int(weight * 30)
                    st.markdown(f"**{t}**: {weight:.2%} `{'\u2588' * bar_len}`")

    with col2:
        if "opt_weights" in st.session_state:
            w = st.session_state["opt_weights"]
            nonzero = {k: v for k, v in w.items() if v > 0.001}
            if nonzero:
                 fig = make_pie_chart(
                     labels=list(nonzero.keys()),
                     values=[v * 100 for v in nonzero.values()],
                     height=400,
                 )
                 st.plotly_chart(fig, use_container_width=True)

with tab_all:
    section_title("All Optimization Strategies Compared")
    if is_beginner():
        st.caption("Run every strategy and see which one gives the best results.")
    else:
        st.caption("Run every strategy at once and compare their suggested allocations and performance.")

    if "all_strategies" not in st.session_state or st.button("Re-run All Strategies"):
        with st.spinner("Running all strategies..."):
            all_strategies = optimize_all_strategies(prices, risk_free_rate=rf)
            st.session_state["all_strategies"] = all_strategies
            st.toast("All strategies computed!", icon="\u2705")

    if "all_strategies" in st.session_state:
        all_s = st.session_state["all_strategies"]

        optimized = {}
        for name, w in all_s.items():
            optimized[name] = build_portfolio_returns(prices, w)
        optimized["Equal Weight"] = build_portfolio_returns(prices, {t: 1.0 / len(tickers) for t in tickers})
        table = metrics_table(optimized, rf=rf)

        rank_col1, rank_col2 = st.columns(2)
        with rank_col1:
            rank_label = "Rank strategies by" if not is_beginner() else "Rank by"
            rank_metric = st.selectbox(rank_label, [
                "Sharpe Ratio", "Sortino Ratio", "Calmar Ratio", "Omega Ratio",
                "Annualized Return", "CAGR", "Annualized Volatility", "Max Drawdown",
                "CVaR (95%)",
            ], index=0, key="rank_metric")
        with rank_col2:
            rank_direction = "higher" if rank_metric in [
                "Sharpe Ratio", "Sortino Ratio", "Calmar Ratio", "Omega Ratio",
                "Annualized Return", "CAGR",
            ] else "lower"
            if is_beginner():
                st.info(f"**{'Higher' if rank_direction == 'higher' else 'Lower'} is better**")
            else:
                st.info(f"**{rank_direction} is better** for {rank_metric}")

        ranked = table[rank_metric].sort_values(ascending=(rank_direction == "lower"))
        best_name = ranked.index[0]
        best_val = ranked.iloc[0]

        if best_name in all_s:
            save_recommended_weights(all_s[best_name], f"Compare All: {best_name} ({rank_metric}={best_val:.4f})")

        st.success(f"\U0001f3c6 **Best: {best_name}** \u2014 {rank_metric}: {best_val:.4f}")
        if is_beginner():
            st.caption("This strategy's weights have been saved for use in simulations.")
        else:
            st.caption("This strategy's weights have been saved as the recommended portfolio (used in Monte Carlo & Backtest).")

        st.markdown("**Ranking:**")
        for i, (name, val) in enumerate(ranked.items()):
            medal = {0: " \U0001f947", 1: " \U0001f948", 2: " \U0001f949"}.get(i, "")
            st.markdown(f"{i+1}. **{name}** \u2014 {rank_metric}: `{val:.4f}`{medal}")

        divider()
        section_title("Full Metrics")

        weights_data = {}
        for name, weights in all_s.items():
            sorted_w = sorted(weights.items(), key=lambda x: x[0])
            weights_data[name] = [w * 100 for _, w in sorted_w]

        fig = make_bar_chart(
            categories=[t for t, _ in sorted_w],
            values_dict=weights_data,
            y_title="Weight %",
            height=600,
        )
        st.plotly_chart(fig, use_container_width=True)

        table.index.name = "Strategy"
        styled = format_dataframe_styler(table)
        st.dataframe(styled, use_container_width=True, height=400)
        render_export_section(table, "optimization_comparison.csv", key="opt_comparison")

        with st.expander("\U0001f4c8 Equity Curves"):
            st.caption("How $10k would have grown under each strategy's allocation.")
            curves = compare_portfolios(optimized, initial_value=10000)
            fig = go.Figure()
            colors = chart_colors(len(curves.columns))
            for i, col in enumerate(curves.columns):
                fig.add_trace(go.Scatter(x=curves.index, y=curves[col], name=col, mode="lines",
                                         line=dict(color=colors[i])))
            apply_theme(fig, height=500)
            st.plotly_chart(fig, use_container_width=True)

with tab_bl:
    col_bl, col_kelly = st.columns(2)

    with col_bl:
        section_title("Black-Litterman")
        if is_beginner():
            st.caption("Start with market defaults, then add your predictions for each investment. "
                        "Set your expected return (%) and confidence for each asset.")
        else:
            st.caption("Start from the market equilibrium, then overlay your personal return expectations. "
                        "Set an expected return (%) and confidence (lower = more uncertain) for each asset.")

        views = {}
        view_confs = []
        for t in tickers:
            c1, c2 = st.columns(2)
            with c1:
                ret_label = f"{t} return (%)" if not is_beginner() else f"{t} expected gain (%)"
                expected = st.number_input(ret_label, value=10.0, step=1.0, key=f"bl_view_{t}",
                                           help="Your expected annual return for this asset." if not is_beginner()
                                           else "What yearly return you expect from this investment.") / 100
            with c2:
                conf = st.number_input(f"{t} conf.", value=0.05, step=0.01, format="%.3f", key=f"bl_conf_{t}",
                                        help="Standard deviation of your view. Lower = more confident.")
            if abs(expected) > 0.001:
                views[t] = expected
                view_confs.append(conf)

        bl_target = st.selectbox("Target", ["max_sharpe", "min_volatility", "max_quadratic_utility"], key="bl_target")

        if st.button("Run Black-Litterman", type="primary"):
            with st.spinner("Running Black-Litterman..."):
                bl_weights = black_litterman_optimize(
                    prices, views=views, view_confidences=view_confs, target=bl_target,
                )
                st.session_state["bl_weights"] = bl_weights
                save_recommended_weights(bl_weights, f"Black-Litterman ({bl_target})")
                st.toast("Black-Litterman complete!", icon="\u2705")

        if "bl_weights" in st.session_state:
            bl_w = st.session_state["bl_weights"]
            nonzero = {k: v for k, v in bl_w.items() if v > 0.001}
            for t, w in sorted(nonzero.items(), key=lambda x: -x[1]):
                bar_len = int(w * 30)
                st.markdown(f"**{t}**: {w:.2%} `{'\u2588' * bar_len}`")
            if nonzero:
                fig = make_pie_chart(list(nonzero.keys()), [v * 100 for v in nonzero.values()],
                                     height=300)
                st.plotly_chart(fig, use_container_width=True)

    with col_kelly:
        section_title("Kelly Criterion")
        if is_beginner():
            st.caption("The mathematically optimal amount to invest in each asset for maximum long-term growth. "
                        "Can be aggressive \u2014 consider using half-Kelly in practice.")
        else:
            st.caption("The mathematically optimal position size to maximize long-term growth. "
                        "Based on mean_return / variance for each asset. Can be aggressive \u2014 consider using half-Kelly in practice.")
        if st.button("Compute Kelly Weights", type="primary"):
            kelly_w = kelly_criterion(prices)
            st.session_state["kelly_weights"] = kelly_w
            save_recommended_weights(kelly_w, "Kelly Criterion")
            st.toast("Kelly weights computed!", icon="\u2705")

        if "kelly_weights" in st.session_state:
            kelly_w = st.session_state["kelly_weights"]
            for t, w in sorted(kelly_w.items(), key=lambda x: -x[1]):
                bar_len = max(0, int(w * 30))
                st.markdown(f"**{t}**: {w:.2%} `{'\u2588' * bar_len}`")
            nonzero = {k: v for k, v in kelly_w.items() if v > 0.001}
            if nonzero:
                fig = make_pie_chart(list(nonzero.keys()), [v * 100 for v in nonzero.values()],
                                     height=300)
                st.plotly_chart(fig, use_container_width=True)

with tab_frontier:
    section_title("Efficient Frontier")
    if is_beginner():
        st.caption("The curve shows the best possible return for each level of risk. "
                    "Dots are your investments. Anything below the curve could be improved.")
    else:
        st.caption("The curved line shows the best possible return for each risk level. "
                    "Individual assets are dots; optimal strategy points are marked with symbols.")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        color_metric = st.selectbox("Color by metric", [
            "sharpe", "sortino", "calmar", "omega", "max_drawdown", "cvar",
        ], index=0, format_func=lambda x: {
            "sharpe": "Sharpe Ratio", "sortino": "Sortino Ratio",
            "calmar": "Calmar Ratio", "omega": "Omega Ratio",
            "max_drawdown": "Max Drawdown", "cvar": "CVaR (95%)",
        }[x])
    with col_f2:
        show_strategies = st.multiselect(
            "Show optimal points",
            ["Max Sharpe", "Min Volatility", "Min CVaR", "Min Semivariance",
             "Semivariance Utility", "Max Quadratic Utility", "HRP", "Kelly Criterion"],
            default=["Max Sharpe", "Min Volatility", "Min CVaR", "HRP"],
        )

    with st.spinner("Computing efficient frontier..."):
        frontier_rets, frontier_risks, max_sharpe_pt, min_vol_pt, strategy_points = efficient_frontier_data(prices, risk_free_rate=rf)
        mu = compute_expected_returns(prices)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=frontier_risks, y=frontier_rets, mode="lines",
        name="Efficient Frontier", line=dict(width=3, color="#00d4aa"),
    ))

    markers = {
        "Max Sharpe": dict(symbol="star", color="green"),
        "Min Volatility": dict(symbol="diamond", color="red"),
        "Min CVaR": dict(symbol="hexagon", color="purple"),
        "Min Semivariance": dict(symbol="square", color="orange"),
        "Semivariance Utility": dict(symbol="triangle-up", color="teal"),
        "Max Quadratic Utility": dict(symbol="cross", color="brown"),
        "HRP": dict(symbol="pentagon", color="magenta"),
        "Kelly Criterion": dict(symbol="x", color="navy"),
    }

    for name in show_strategies:
        if name in strategy_points:
            pt = strategy_points[name]
            m = markers.get(name, dict(symbol="circle", color="gray"))
            metric_val = pt.get(color_metric, 0)
            fig.add_trace(go.Scatter(
                x=[pt["risk"]], y=[pt["return"]], mode="markers+text",
                name=f"{name} ({color_metric}: {metric_val:.3f})",
                marker=dict(size=14, symbol=m["symbol"], color=m["color"]),
                text=[name], textposition="top center",
            ))

    colors = chart_colors(len(prices.columns))
    for i, t in enumerate(prices.columns):
        ann_vol = returns[t].std() * np.sqrt(252)
        ann_ret = mu.get(t, 0)
        fig.add_trace(go.Scatter(
            x=[ann_vol], y=[ann_ret], mode="markers+text", name=t,
            text=[t], textposition="top center",
            marker=dict(size=10, color=colors[i]),
        ))
    fig.update_layout(
        xaxis_title="Annualized Volatility", yaxis_title="Annualized Expected Return",
    )
    apply_theme(fig, height=700)
    st.plotly_chart(fig, use_container_width=True)

    if strategy_points:
        summary = {}
        for name, pt in strategy_points.items():
            summary[name] = {
                "Return": f"{pt['return']:.2%}",
                "Risk": f"{pt['risk']:.2%}",
                "Sharpe": f"{pt['sharpe']:.3f}",
                "Sortino": f"{pt['sortino']:.3f}",
                "Calmar": f"{pt['calmar']:.3f}",
                "Omega": f"{pt['omega']:.3f}",
                "Max DD": f"{pt['max_drawdown']:.2%}",
                "CVaR": f"{pt['cvar']:.4f}",
            }
        st.dataframe(pd.DataFrame(summary), use_container_width=True, height=300)

divider()
render_recommended_portfolio(prices, returns, tickers, rf)
divider()
render_next_button("Backtest", "4_Backtest.py")
