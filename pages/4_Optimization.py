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
    compute_covariance, OPTIMIZATION_TARGETS,
)
from src.portfolio import build_portfolio_returns, compare_portfolios
from src.metrics import metrics_table
from src.ui import (
    init_shared_state, require_data, render_workflow_stepper,
    render_next_button, render_portfolio_info, save_recommended_weights,
    render_recommended_portfolio,
)

st.set_page_config(page_title="Optimization", layout="wide")
init_shared_state()
render_workflow_stepper(4)

st.title("Portfolio Optimization")
require_data()

prices = st.session_state["prices"]
returns = st.session_state["returns"]
tickers = st.session_state.get("tickers", [])
rf = st.session_state.get("risk_free_rate", 0.04)

TARGET_DESCRIPTIONS = {
    "max_sharpe": "Maximize Sharpe ratio",
    "min_volatility": "Minimize portfolio volatility",
    "max_quadratic_utility": "Maximize quadratic utility (risk-averse)",
    "efficient_return": "Minimize risk for target return",
    "efficient_risk": "Maximize return for target risk",
    "min_cvar": "Minimize Conditional Value-at-Risk (95%)",
    "min_semivariance": "Minimize semivariance (downside risk)",
    "semivariance_utility": "Quadratic utility under semivariance (downside risk model)",
    "max_return_min_risk": "Max Sharpe with L2 regularization (more diversified)",
    "hrp": "Hierarchical Risk Parity",
}

with st.sidebar:
    render_portfolio_info()
    st.markdown("---")

with st.expander("What is portfolio optimization?"):
    st.markdown("""
    **Portfolio optimization** uses math to find the asset allocation that best achieves a specific goal (max return, min risk, etc.) based on historical data. Below is every method available in this app:

    ---

    ### Mean-Variance Methods (Markowitz framework)
    These use estimated returns and a covariance matrix to find optimal weights.

    - **max_sharpe (Tangency Portfolio)** — Finds the portfolio with the highest Sharpe ratio. This is the point on the efficient frontier where the capital market line is tangent. **Best when:** you want the best bang-for-your-buck in risk-adjusted terms. This is the most commonly used optimization.

    - **min_volatility (Global Minimum Variance)** — Finds the portfolio with the lowest possible volatility, regardless of return. **Best when:** you're risk-averse and want the smoothest ride possible. Often surprisingly decent returns because low-vol assets tend to outperform expectations.

    - **max_quadratic_utility** — Maximizes a utility function U = return - (risk_aversion/2) × variance. Balances return vs risk based on your risk tolerance. **Best when:** you want a customizable trade-off between return and risk (higher risk_aversion = more conservative).

    - **efficient_return** — Given a target annual return, finds the portfolio with the lowest volatility that achieves it. **Best when:** you have a specific return goal (e.g. "I need at least 8%/year") and want the safest way to get there.

    - **efficient_risk** — Given a target volatility, finds the portfolio with the highest return within that risk budget. **Best when:** you know your max tolerable risk (e.g. "I can stomach 15% annual swings") and want the best return within that constraint.

    - **max_return_min_risk (Regularized Sharpe)** — Same as max_sharpe but adds L2 regularization, which penalizes extreme weights and produces more diversified portfolios. **Best when:** max_sharpe gives you overly concentrated allocations (e.g. 90% in one asset). The regularization spreads weights more evenly.

    ---

    ### Downside Risk Methods
    These focus on protecting against losses rather than minimizing all volatility.

    - **min_cvar (Conditional Value-at-Risk)** — Minimizes the expected loss in the worst 5% of days. Unlike VaR which only tells you the threshold, CVaR tells you how bad it gets *beyond* that threshold. **Best when:** you're worried about tail risk / black swan events / market crashes.

    - **min_semivariance** — Minimizes semivariance, which only measures volatility from negative returns (downside). Ignores upside volatility entirely. **Best when:** you don't care about big gains — you only want to minimize the frequency and severity of losses.

    - **semivariance_utility** — Maximizes quadratic utility under a semivariance risk model. Like max_quadratic_utility but only penalizes downside moves instead of all volatility. **Best when:** you want the best return-to-downside-risk trade-off using a utility framework.

    ---

    ### Machine Learning / Alternative Methods

    - **hrp (Hierarchical Risk Parity)** — Uses hierarchical clustering to group correlated assets, then allocates capital based on the cluster structure. Doesn't require return estimates at all — only the covariance matrix. **Best when:** you want robust diversification without trusting return estimates, which are notoriously noisy. Much more stable than mean-variance across different time periods.

    ---

    ### Position Sizing Methods

    - **Kelly Criterion** — Computes the optimal bet size for each asset as: mean_return / variance. Mathematically maximizes long-term geometric growth (log wealth). **Best when:** you want theoretically optimal compounding. **Warning:** can produce extreme concentrated positions. Many practitioners use "half-Kelly" (halve the weights) for more conservative sizing.

    ---

    ### View-Based Methods

    - **Black-Litterman** — Starts from the market equilibrium (market-cap weighted portfolio), then adjusts based on your personal return expectations ("views") and your confidence in each view. The output blends your views with the market's implied returns. **Best when:** you have strong convictions about specific assets and want a structured way to incorporate them without going all-in.

    ---

    ### Efficient Frontier

    The **efficient frontier** is the curved line plotting the best possible return for each level of risk. Every portfolio *below* the line is sub-optimal — you could get more return for the same risk. The frontier is computed by running `efficient_return` across a range of target returns.
    """)

tab_single, tab_all, tab_bl, tab_frontier = st.tabs(
    ["Single Target", "Compare All", "Black-Litterman & Kelly", "Efficient Frontier"]
)

with tab_single:
    st.subheader("Choose Optimization Target")
    col1, col2 = st.columns([1, 2])

    with col1:
        target = st.selectbox(
            "Optimize for",
            OPTIMIZATION_TARGETS + ["hrp"],
            format_func=lambda x: f"{x} — {TARGET_DESCRIPTIONS.get(x, '')}",
            help="Pick what 'best' means. Different targets suit different goals."
        )
        st.info(f"**{target}**: {TARGET_DESCRIPTIONS.get(target, '')}")

        target_value = None
        if target == "efficient_return":
            mu = compute_expected_returns(prices)
            target_value = st.slider("Target annual return (%)",
                                     float(mu.min() * 100), float(mu.max() * 100),
                                     float(mu.mean() * 100), step=0.5,
                                     help="Set the minimum annual return you want, and the optimizer finds the lowest-risk way to achieve it.") / 100
        elif target == "efficient_risk":
            target_value = st.slider("Target annual volatility (%)", 5.0, 50.0, 20.0, step=0.5,
                                     help="Set the max volatility you can tolerate, and the optimizer maximizes return within that risk budget.") / 100

        if st.button("Optimize", type="primary"):
            with st.spinner("Optimizing..."):
                if target == "hrp":
                    w = optimize_portfolio(prices, target="hrp")
                else:
                    w = optimize_portfolio(prices, target=target, target_value=target_value, risk_free_rate=rf)
                st.session_state["opt_weights"] = w
                save_recommended_weights(w, f"Single: {target}")

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
            fig = go.Figure(go.Pie(labels=list(nonzero.keys()), values=list(nonzero.values()), hole=0.4))
            fig.update_layout(title="Portfolio Allocation", template="plotly_dark", height=400)
            st.plotly_chart(fig, use_container_width=True)

with tab_all:
    st.subheader("All Optimization Strategies Compared")
    st.caption("Run every strategy at once and compare their suggested allocations and performance.")

    if "all_strategies" not in st.session_state or st.button("Re-run All Strategies"):
        with st.spinner("Running all strategies..."):
            all_strategies = optimize_all_strategies(prices, risk_free_rate=rf)
            st.session_state["all_strategies"] = all_strategies

    if "all_strategies" in st.session_state:
        all_s = st.session_state["all_strategies"]

        optimized = {}
        for name, w in all_s.items():
            optimized[name] = build_portfolio_returns(prices, w)
        optimized["Equal Weight"] = build_portfolio_returns(prices, {t: 1.0 / len(tickers) for t in tickers})
        table = metrics_table(optimized, rf=rf)

        rank_col1, rank_col2 = st.columns(2)
        with rank_col1:
            rank_metric = st.selectbox("Rank strategies by", [
                "Sharpe Ratio", "Sortino Ratio", "Calmar Ratio", "Omega Ratio",
                "Annualized Return", "CAGR", "Annualized Volatility", "Max Drawdown",
                "CVaR (95%)",
            ], index=0, key="rank_metric",
                help="Pick which metric defines 'best'. Higher is better for ratios/returns, lower is better for volatility/drawdown/CVaR.")
        with rank_col2:
            rank_direction = "higher" if rank_metric in [
                "Sharpe Ratio", "Sortino Ratio", "Calmar Ratio", "Omega Ratio",
                "Annualized Return", "CAGR",
            ] else "lower"
            st.info(f"**{rank_direction} is better** for {rank_metric}")

        ranked = table[rank_metric].sort_values(ascending=(rank_direction == "lower"))
        best_name = ranked.index[0]
        best_val = ranked.iloc[0]

        if best_name in all_s:
            save_recommended_weights(all_s[best_name], f"Compare All: {best_name} ({rank_metric}={best_val:.4f})")

        st.success(f"**Best: {best_name}** — {rank_metric}: {best_val:.4f}")
        st.caption("This strategy's weights have been saved as the recommended portfolio (used in Monte Carlo & Backtest).")

        st.markdown("**Ranking:**")
        for i, (name, val) in enumerate(ranked.items()):
            medal = {0: " :1st_place_medal:", 1: " :2nd_place_medal:", 2: " :3rd_place_medal:"}.get(i, "")
            st.markdown(f"{i+1}. **{name}** — {rank_metric}: `{val:.4f}`{medal}")

        st.markdown("---")
        st.subheader("Full Metrics")

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
            barmode="group", template="plotly_dark", height=600,
        )
        st.plotly_chart(fig, use_container_width=True)

        table.index.name = "Strategy"
        st.dataframe(table.style.format("{:.4f}"), use_container_width=True, height=400)
        csv = table.to_csv()
        st.download_button("Download CSV", csv, "optimization_comparison.csv", "text/csv")

        with st.expander("Equity Curves"):
            st.caption("How $10k would have grown under each strategy's allocation.")
            curves = compare_portfolios(optimized, initial_value=10000)
            fig = go.Figure()
            for col in curves.columns:
                fig.add_trace(go.Scatter(x=curves.index, y=curves[col], name=col, mode="lines"))
            fig.update_layout(title="Strategy Equity Curves ($10k initial)", template="plotly_dark", height=500)
            st.plotly_chart(fig, use_container_width=True)

with tab_bl:
    col_bl, col_kelly = st.columns(2)

    with col_bl:
        st.subheader("Black-Litterman")
        st.caption("Start from the market equilibrium, then overlay your personal return expectations. "
                    "Set an expected return (%) and confidence (lower = more uncertain) for each asset.")

        views = {}
        view_confs = []
        for t in tickers:
            c1, c2 = st.columns(2)
            with c1:
                expected = st.number_input(f"{t} return (%)", value=10.0, step=1.0, key=f"bl_view_{t}",
                                            help="Your expected annual return for this asset.") / 100
            with c2:
                conf = st.number_input(f"{t} conf.", value=0.05, step=0.01, format="%.3f", key=f"bl_conf_{t}",
                                        help="Standard deviation of your view. Lower = more confident. 0.05 = 5% uncertainty.")
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

        if "bl_weights" in st.session_state:
            bl_w = st.session_state["bl_weights"]
            nonzero = {k: v for k, v in bl_w.items() if v > 0.001}
            for t, w in sorted(nonzero.items(), key=lambda x: -x[1]):
                st.markdown(f"**{t}**: {w:.2%}")
            fig = go.Figure(go.Pie(labels=list(nonzero.keys()), values=list(nonzero.values()), hole=0.4))
            fig.update_layout(title="BL Allocation", template="plotly_dark", height=300)
            st.plotly_chart(fig, use_container_width=True)

    with col_kelly:
        st.subheader("Kelly Criterion")
        st.caption("The mathematically optimal position size to maximize long-term growth. "
                    "Based on mean return / variance for each asset. Can be aggressive — consider using half-Kelly in practice.")
        if st.button("Compute Kelly Weights", type="primary"):
            kelly_w = kelly_criterion(prices)
            st.session_state["kelly_weights"] = kelly_w
            save_recommended_weights(kelly_w, "Kelly Criterion")

        if "kelly_weights" in st.session_state:
            kelly_w = st.session_state["kelly_weights"]
            for t, w in sorted(kelly_w.items(), key=lambda x: -x[1]):
                st.markdown(f"**{t}**: {w:.2%}")
            nonzero = {k: v for k, v in kelly_w.items() if v > 0.001}
            if nonzero:
                fig = go.Figure(go.Pie(labels=list(nonzero.keys()), values=list(nonzero.values()), hole=0.4))
                fig.update_layout(title="Kelly Allocation", template="plotly_dark", height=300)
                st.plotly_chart(fig, use_container_width=True)

with tab_frontier:
    st.subheader("Efficient Frontier")
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

    for t in prices.columns:
        ann_vol = returns[t].std() * np.sqrt(252)
        ann_ret = mu.get(t, 0)
        fig.add_trace(go.Scatter(
            x=[ann_vol], y=[ann_ret], mode="markers+text", name=t,
            text=[t], textposition="top center", marker=dict(size=10),
        ))
    fig.update_layout(
        title=f"Efficient Frontier (colored by {color_metric})",
        xaxis_title="Annualized Volatility", yaxis_title="Annualized Expected Return",
        template="plotly_dark", height=700,
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

st.markdown("---")
render_recommended_portfolio(prices, returns, tickers, rf)
st.markdown("---")
render_next_button("Monte Carlo", "5_Monte_Carlo.py")
