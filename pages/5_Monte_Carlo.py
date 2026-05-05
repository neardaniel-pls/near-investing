import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.portfolio import build_portfolio_returns
from src.monte_carlo import (
    simulate_portfolio_monte_carlo,
    simulate_historical_bootstrap,
    monte_carlo_statistics,
    monte_carlo_return_stats,
)

st.set_page_config(page_title="Monte Carlo", layout="wide")
st.title("Monte Carlo Simulation")

if "returns" not in st.session_state:
    st.warning("Go to **Overview** first to fetch data.")
    st.stop()

prices = st.session_state["prices"]
returns = st.session_state["returns"]
tickers = st.session_state.get("tickers", [])

with st.sidebar:
    st.header("Portfolio Weights")
    weights = {}
    for t in tickers:
        default = round(100 / len(tickers))
        w = st.slider(f"{t} %", 0, 100, default, key=f"mc_{t}")
        weights[t] = w / 100
    total = sum(weights.values())
    if abs(total - 1.0) > 0.01:
        st.error(f"Weights sum to {total:.0%}")

    st.markdown("---")
    n_sims = st.selectbox("Number of simulations", [1000, 5000, 10000, 50000], index=2)
    n_days = st.selectbox("Simulation period (trading days)", [63, 126, 252, 504, 1260], index=2)
    initial_value = st.number_input("Initial investment ($)", value=10000, min_value=100)
    seed = st.number_input("Random seed", value=42)

portfolio_rets = build_portfolio_returns(prices, weights)

tab_param, tab_bootstrap, tab_stats, tab_compare = st.tabs(
    ["Parametric", "Historical Bootstrap", "Statistics", "Compare Portfolios"]
)

with tab_param:
    st.subheader(f"Parametric Monte Carlo ({n_sims:,} simulations, {n_days} days)")
    paths = simulate_portfolio_monte_carlo(
        portfolio_rets, n_simulations=n_sims, n_days=n_days,
        initial_value=initial_value, random_seed=seed,
    )

    n_show = min(200, paths.shape[1])
    fig = go.Figure()
    for i in range(n_show):
        fig.add_trace(go.Scatter(
            y=paths[:, i], mode="lines",
            line=dict(width=0.5, color="rgba(100,100,255,0.08)"),
            showlegend=False,
        ))
    mean_path = np.mean(paths, axis=1)
    p5 = np.percentile(paths, 5, axis=1)
    p95 = np.percentile(paths, 95, axis=1)
    fig.add_trace(go.Scatter(y=p95, mode="lines", name="95th %ile", line=dict(width=1, color="green", dash="dash")))
    fig.add_trace(go.Scatter(y=mean_path, mode="lines", name="Mean", line=dict(width=3, color="red")))
    fig.add_trace(go.Scatter(y=p5, mode="lines", name="5th %ile", line=dict(width=1, color="red", dash="dash")))
    fig.add_hline(y=initial_value, line_dash="dash", line_color="gray")
    fig.update_layout(
        title="Parametric Monte Carlo", yaxis_title="Portfolio Value ($)",
        xaxis_title="Trading Days", template="plotly_white", height=600,
    )
    st.plotly_chart(fig, use_container_width=True)

with tab_bootstrap:
    st.subheader(f"Historical Bootstrap ({n_sims:,} simulations, {n_days} days)")
    bootstrap_paths = simulate_historical_bootstrap(
        portfolio_rets, n_simulations=n_sims, n_days=n_days,
        initial_value=initial_value, random_seed=seed,
    )

    n_show = min(200, bootstrap_paths.shape[1])
    fig = go.Figure()
    for i in range(n_show):
        fig.add_trace(go.Scatter(
            y=bootstrap_paths[:, i], mode="lines",
            line=dict(width=0.5, color="rgba(100,200,100,0.08)"),
            showlegend=False,
        ))
    mean_path = np.mean(bootstrap_paths, axis=1)
    fig.add_trace(go.Scatter(y=mean_path, mode="lines", name="Mean", line=dict(width=3, color="red")))
    fig.add_hline(y=initial_value, line_dash="dash", line_color="gray")
    fig.update_layout(
        title="Historical Bootstrap", yaxis_title="Portfolio Value ($)",
        xaxis_title="Trading Days", template="plotly_white", height=600,
    )
    st.plotly_chart(fig, use_container_width=True)

with tab_stats:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Parametric Statistics")
        param_stats = monte_carlo_statistics(paths)
        for k, v in param_stats.items():
            st.markdown(f"**{k}**: ${v:,.2f}")

    with col2:
        st.subheader("Bootstrap Statistics")
        boot_stats = monte_carlo_statistics(bootstrap_paths)
        for k, v in boot_stats.items():
            st.markdown(f"**{k}**: ${v:,.2f}")

    st.markdown("---")
    st.subheader("Return Statistics")
    col1, col2 = st.columns(2)
    with col1:
        param_ret = monte_carlo_return_stats(paths, initial_value)
        for k, v in param_ret.items():
            st.markdown(f"**{k}**: {v:.4f}")
    with col2:
        boot_ret = monte_carlo_return_stats(bootstrap_paths, initial_value)
        for k, v in boot_ret.items():
            st.markdown(f"**{k}**: {v:.4f}")

    st.subheader("Final Value Distribution")
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Parametric", "Bootstrap"))
    fig.add_trace(go.Histogram(x=paths[-1, :], nbinsx=100, name="Parametric", marker_color="blue", opacity=0.7), row=1, col=1)
    fig.add_trace(go.Histogram(x=bootstrap_paths[-1, :], nbinsx=100, name="Bootstrap", marker_color="green", opacity=0.7), row=1, col=2)
    for i in [1, 2]:
        fig.add_vline(x=initial_value, line_dash="dash", line_color="red", row=1, col=i)
    fig.update_layout(template="plotly_white", height=400)
    st.plotly_chart(fig, use_container_width=True)

with tab_compare:
    st.subheader("Compare Portfolios Under Stress")
    n_allocs = st.number_input("Number of allocations to compare", value=3, min_value=2, max_value=5)

    allocs = {}
    for i in range(n_allocs):
        with st.expander(f"Allocation {i + 1}", expanded=(i == 0)):
            name = st.text_input("Name", value=["Conservative", "Balanced", "Aggressive", "Growth", "Speculative"][i], key=f"mc_name_{i}")
            alloc_w = {}
            for t in tickers:
                alloc_w[t] = st.slider(f"{t} %", 0, 100, round(100 / len(tickers)), key=f"mc_alloc_{i}_{t}") / 100
            allocs[name] = alloc_w

    if st.button("Run Comparison", type="primary"):
        results = {}
        for name, alloc_w in allocs.items():
            ret = build_portfolio_returns(prices, alloc_w)
            sim = simulate_portfolio_monte_carlo(
                ret, n_simulations=min(n_sims, 5000), n_days=n_days,
                initial_value=initial_value, random_seed=seed,
            )
            results[name] = monte_carlo_return_stats(sim, initial_value)

        comparison_df = pd.DataFrame(results)
        st.dataframe(comparison_df.style.format("{:.4f}"), use_container_width=True)

        metrics_to_plot = ["Mean Return", "Std Return", "Avg Max Drawdown", "Probability of Loss"]
        fig = go.Figure()
        for metric in metrics_to_plot:
            fig.add_trace(go.Bar(
                x=list(results.keys()),
                y=[results[k][metric] for k in results],
                name=metric,
            ))
        fig.update_layout(title="Monte Carlo Comparison", barmode="group", template="plotly_white", height=500)
        st.plotly_chart(fig, use_container_width=True)
