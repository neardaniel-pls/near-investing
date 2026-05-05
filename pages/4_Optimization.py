import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.optimization import (
    optimize_portfolio, optimize_all_strategies,
    black_litterman_optimize, kelly_criterion,
    efficient_frontier_data, compute_expected_returns,
    compute_covariance, OPTIMIZATION_TARGETS,
)
from src.portfolio import build_portfolio_returns, compare_portfolios
from src.metrics import metrics_table

st.set_page_config(page_title="Optimization", layout="wide")
st.title("Portfolio Optimization")

if "returns" not in st.session_state:
    st.warning("Go to **Overview** first to fetch data.")
    st.stop()

prices = st.session_state["prices"]
returns = st.session_state["returns"]
tickers = st.session_state.get("tickers", [])

TARGET_DESCRIPTIONS = {
    "max_sharpe": "Maximize Sharpe ratio",
    "min_volatility": "Minimize portfolio volatility",
    "max_quadratic_utility": "Maximize quadratic utility (risk-averse)",
    "efficient_return": "Minimize risk for target return",
    "efficient_risk": "Maximize return for target risk",
    "min_cvar": "Minimize Conditional Value-at-Risk (95%)",
    "min_semivariance": "Minimize semivariance (downside risk)",
    "max_sortino": "Maximize Sortino-oriented utility",
    "max_return_min_risk": "Max Sharpe with L2 regularization (more diversified)",
    "hrp": "Hierarchical Risk Parity",
}

tab_single, tab_all, tab_bl, tab_frontier = st.tabs(
    ["Single Target", "Compare All", "Black-Litterman", "Efficient Frontier"]
)

rf = st.sidebar.number_input("Risk-free rate (%)", value=4.0, min_value=0.0, max_value=20.0, step=0.5, key="opt_rf") / 100

with tab_single:
    st.subheader("Choose Optimization Target")
    col1, col2 = st.columns([1, 2])

    with col1:
        target = st.selectbox(
            "Optimize for",
            OPTIMIZATION_TARGETS + ["hrp"],
            format_func=lambda x: f"{x} — {TARGET_DESCRIPTIONS.get(x, '')}",
        )
        st.info(f"**{target}**: {TARGET_DESCRIPTIONS.get(target, '')}")

        target_value = None
        if target == "efficient_return":
            mu = compute_expected_returns(prices)
            target_value = st.slider("Target annual return (%)",
                                     float(mu.min() * 100), float(mu.max() * 100),
                                     float(mu.mean() * 100), step=0.5) / 100
        elif target == "efficient_risk":
            target_value = st.slider("Target annual volatility (%)", 5.0, 50.0, 20.0, step=0.5) / 100

        if st.button("Optimize", type="primary"):
            with st.spinner("Optimizing..."):
                if target == "hrp":
                    w = optimize_portfolio(prices, target="hrp")
                else:
                    w = optimize_portfolio(prices, target=target, target_value=target_value, risk_free_rate=rf)
                st.session_state["opt_weights"] = w

        if "opt_weights" in st.session_state:
            w = st.session_state["opt_weights"]
            st.subheader("Optimal Weights")
            for t, weight in sorted(w.items(), key=lambda x: -x[1]):
                if abs(weight) > 0.001:
                    st.markdown(f"**{t}**: {weight:.2%}")

    with col2:
        if "opt_weights" in st.session_state:
            w = st.session_state["opt_weights"]
            nonzero = {k: v for k, v in w.items() if v > 0.001}
            fig = go.Figure(go.Pie(labels=list(nonzero.keys()), values=list(nonzero.values())))
            fig.update_layout(title="Portfolio Allocation", template="plotly_white", height=400)
            st.plotly_chart(fig, use_container_width=True)

with tab_all:
    st.subheader("All Optimization Strategies Compared")
    if st.button("Run All Strategies", type="primary"):
        with st.spinner("Running all strategies..."):
            all_strategies = optimize_all_strategies(prices, risk_free_rate=rf)
            st.session_state["all_strategies"] = all_strategies

    if "all_strategies" in st.session_state:
        all_s = st.session_state["all_strategies"]

        fig = go.Figure()
        for name, weights in all_s.items():
            sorted_w = sorted(weights.items(), key=lambda x: x[0])
            fig.add_trace(go.Bar(
                x=[t for t, _ in sorted_w],
                y=[w * 100 for _, w in sorted_w],
                name=name,
            ))
        fig.update_layout(
            title="Optimal Weights by Strategy (%)", yaxis_title="Weight %",
            barmode="group", template="plotly_white", height=600,
        )
        st.plotly_chart(fig, use_container_width=True)

        optimized = {}
        for name, w in all_s.items():
            optimized[name] = build_portfolio_returns(prices, w)
        optimized["Equal Weight"] = build_portfolio_returns(prices, {t: 1.0 / len(tickers) for t in tickers})
        table = metrics_table(optimized)
        st.dataframe(table.style.format("{:.4f}"), use_container_width=True, height=400)

        curves = compare_portfolios(optimized, initial_value=10000)
        fig = go.Figure()
        for col in curves.columns:
            fig.add_trace(go.Scatter(x=curves.index, y=curves[col], name=col, mode="lines"))
        fig.update_layout(title="Strategy Equity Curves ($10k initial)", template="plotly_white", height=500)
        st.plotly_chart(fig, use_container_width=True)

with tab_bl:
    st.subheader("Black-Litterman Model")
    st.markdown("Set your expected returns for specific assets (your market views).")

    views = {}
    view_confs = []
    for t in tickers:
        col1, col2 = st.columns(2)
        with col1:
            expected = st.number_input(f"{t} expected return (%)", value=10.0, step=1.0, key=f"bl_view_{t}") / 100
        with col2:
            conf = st.number_input(f"{t} confidence (std)", value=0.05, step=0.01, format="%.3f", key=f"bl_conf_{t}")
        if abs(expected) > 0.001:
            views[t] = expected
            view_confs.append(conf)

    bl_target = st.selectbox("Optimization target", ["max_sharpe", "min_volatility", "max_quadratic_utility"], key="bl_target")

    if st.button("Run Black-Litterman", type="primary"):
        with st.spinner("Running Black-Litterman..."):
            bl_weights = black_litterman_optimize(
                prices, views=views, view_confidences=view_confs, target=bl_target,
            )
            st.session_state["bl_weights"] = bl_weights

    if "bl_weights" in st.session_state:
        bl_w = st.session_state["bl_weights"]
        nonzero = {k: v for k, v in bl_w.items() if v > 0.001}
        col1, col2 = st.columns(2)
        with col1:
            for t, w in sorted(nonzero.items(), key=lambda x: -x[1]):
                st.markdown(f"**{t}**: {w:.2%}")
        with col2:
            fig = go.Figure(go.Pie(labels=list(nonzero.keys()), values=list(nonzero.values())))
            fig.update_layout(title="Black-Litterman Allocation", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Kelly Criterion")
    if st.button("Compute Kelly Weights"):
        kelly_w = kelly_criterion(prices)
        for t, w in sorted(kelly_w.items(), key=lambda x: -x[1]):
            st.markdown(f"**{t}**: {w:.2%}")

with tab_frontier:
    st.subheader("Efficient Frontier")

    color_metric = st.selectbox("Color strategies by metric", [
        "sharpe", "sortino", "calmar", "omega", "max_drawdown", "cvar",
    ], index=0, format_func=lambda x: {
        "sharpe": "Sharpe Ratio", "sortino": "Sortino Ratio",
        "calmar": "Calmar Ratio", "omega": "Omega Ratio",
        "max_drawdown": "Max Drawdown", "cvar": "CVaR (95%)",
    }[x])

    show_strategies = st.multiselect(
        "Show optimal points",
        ["Max Sharpe", "Min Volatility", "Min CVaR", "Min Semivariance",
         "Max Sortino", "Max Quadratic Utility", "HRP", "Kelly Criterion"],
        default=["Max Sharpe", "Min Volatility", "Min CVaR", "HRP"],
    )

    with st.spinner("Computing efficient frontier..."):
        frontier_rets, frontier_risks, max_sharpe_pt, min_vol_pt, strategy_points = efficient_frontier_data(prices, risk_free_rate=rf)
        mu = compute_expected_returns(prices)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=frontier_risks, y=frontier_rets, mode="lines",
        name="Efficient Frontier", line=dict(width=3, color="blue"),
    ))

    markers = {
        "Max Sharpe": dict(symbol="star", color="green"),
        "Min Volatility": dict(symbol="diamond", color="red"),
        "Min CVaR": dict(symbol="hexagon", color="purple"),
        "Min Semivariance": dict(symbol="square", color="orange"),
        "Max Sortino": dict(symbol="triangle-up", color="teal"),
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

    for t in prices.columns:
        ann_vol = returns[t].std() * np.sqrt(252)
        ann_ret = mu.get(t, 0)
        fig.add_trace(go.Scatter(
            x=[ann_vol], y=[ann_ret], mode="markers+text", name=t,
            text=[t], textposition="top center", marker=dict(size=10),
        ))
    fig.update_layout(
        title=f"Efficient Frontier (colored by {color_metric})",
        xaxis_title="Annualized Volatility",
        yaxis_title="Annualized Expected Return",
        template="plotly_white", height=700,
    )
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
