import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.portfolio import build_portfolio_returns
from src.monte_carlo import (
    simulate_portfolio_monte_carlo,
    simulate_historical_bootstrap,
    simulate_multivariate_monte_carlo,
    monte_carlo_statistics,
    monte_carlo_return_stats,
)
from src.ui import (
    init_shared_state, require_data, render_workflow_stepper,
    render_next_button, render_portfolio_info, render_weight_sliders,
)

st.set_page_config(page_title="Monte Carlo", layout="wide")
init_shared_state()
render_workflow_stepper(5)

st.title("Monte Carlo Simulation")
require_data()

prices = st.session_state["prices"]
returns = st.session_state["returns"]
tickers = st.session_state.get("tickers", [])
initial_value = st.session_state.get("initial_investment", 10000)

rec_weights = st.session_state.get("recommended_weights")
rec_label = st.session_state.get("recommended_label", "")

with st.sidebar:
    render_portfolio_info()
    st.markdown("---")

    if rec_weights:
        st.success(f"Optimized: **{rec_label}**")
        st.caption("Weights auto-loaded from Optimization. Adjust below or click 'Use Optimized' to reset.")
    else:
        st.info("No optimization run yet. Set weights manually or run Optimization first.")

    default_w = {t: round(v * 100) for t, v in rec_weights.items()} if rec_weights else None
    weights, weights_valid = render_weight_sliders(
        tickers, key_prefix="mc", default_weights=default_w,
    )

    st.markdown("---")
    n_sims = st.selectbox("Simulations", [1000, 5000, 10000, 50000], index=2,
                           help="More simulations = more accurate estimates but slower.")
    n_days = st.selectbox("Period (trading days)", [63, 126, 252, 504, 1260], index=2,
                           help="252 = ~1 year, 504 = ~2 years, 1260 = ~5 years.")
    seed = st.number_input("Random seed", value=42,
                            help="Fixed seed means reproducible results. Change it for different random scenarios.")
    use_multivariate = st.checkbox("Use multivariate simulation",
                                    help="Simulate each asset independently then combine (captures correlations). "
                                    "Uncheck to simulate the portfolio as a single return series (faster).")

if not weights_valid:
    st.stop()

with st.expander("What is Monte Carlo simulation?"):
    st.markdown("""
    **Monte Carlo** generates thousands of possible future scenarios to stress-test your portfolio.

    - **Parametric** — assumes returns follow a normal (bell curve) distribution with the same mean and volatility as history. Good for quick estimates but underestimates extreme events.
    - **Historical Bootstrap** — randomly picks actual past daily returns to build scenarios. Captures fat tails and real-world patterns better.

    **Key outputs:**
    - **VaR (Value at Risk)** — the portfolio value at the 5th percentile. "There's a 95% chance you'll have at least this much."
    - **CVaR** — the average outcome in the worst 5% of scenarios. More conservative than VaR.
    - **Probability of Loss** — % of scenarios where you end up with less than you started.
    """)

if rec_weights:
    st.caption(f"Simulating with weights from: **{rec_label}**")

portfolio_rets = build_portfolio_returns(prices, weights)

with st.spinner("Running simulations..."):
    if use_multivariate:
        paths = simulate_multivariate_monte_carlo(
            prices, weights, n_simulations=n_sims, n_days=n_days,
            initial_value=initial_value, random_seed=seed, use_historical=False,
        )
    else:
        portfolio_rets = build_portfolio_returns(prices, weights)
        paths = simulate_portfolio_monte_carlo(
            portfolio_rets, n_simulations=n_sims, n_days=n_days,
            initial_value=initial_value, random_seed=seed,
        )
    bootstrap_paths = simulate_historical_bootstrap(
        build_portfolio_returns(prices, weights), n_simulations=n_sims, n_days=n_days,
        initial_value=initial_value, random_seed=seed,
    )

col_param, col_boot = st.columns(2)

with col_param:
    st.subheader("Parametric Monte Carlo")
    if use_multivariate:
        st.caption("Simulated paths using multivariate normal distribution (captures asset correlations).")
    else:
        st.caption("Simulated paths assuming normal distribution of returns.")
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
    fig.add_trace(go.Scatter(y=mean_path, mode="lines", name="Mean", line=dict(width=3, color="#00d4aa")))
    fig.add_trace(go.Scatter(y=p5, mode="lines", name="5th %ile", line=dict(width=1, color="red", dash="dash")))
    fig.add_hline(y=initial_value, line_dash="dash", line_color="gray")
    fig.update_layout(
        yaxis_title="Value ($)", xaxis_title="Trading Days",
        template="plotly_dark", height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

with col_boot:
    st.subheader("Historical Bootstrap")
    st.caption("Simulated paths using actual past returns — captures real-world extreme events.")
    n_show_b = min(200, bootstrap_paths.shape[1])
    fig = go.Figure()
    for i in range(n_show_b):
        fig.add_trace(go.Scatter(
            y=bootstrap_paths[:, i], mode="lines",
            line=dict(width=0.5, color="rgba(100,200,100,0.08)"),
            showlegend=False,
        ))
    mean_path_b = np.mean(bootstrap_paths, axis=1)
    p5_b = np.percentile(bootstrap_paths, 5, axis=1)
    p95_b = np.percentile(bootstrap_paths, 95, axis=1)
    fig.add_trace(go.Scatter(y=p95_b, mode="lines", name="95th %ile", line=dict(width=1, color="green", dash="dash")))
    fig.add_trace(go.Scatter(y=mean_path_b, mode="lines", name="Mean", line=dict(width=3, color="#00d4aa")))
    fig.add_trace(go.Scatter(y=p5_b, mode="lines", name="5th %ile", line=dict(width=1, color="red", dash="dash")))
    fig.add_hline(y=initial_value, line_dash="dash", line_color="gray")
    fig.update_layout(
        yaxis_title="Value ($)", xaxis_title="Trading Days",
        template="plotly_dark", height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

st.subheader("Statistics")
st.caption("Key stats from both simulation methods. Compare parametric (theoretical) vs bootstrap (empirical).")
param_stats = monte_carlo_statistics(paths)
boot_stats = monte_carlo_statistics(bootstrap_paths)
param_ret = monte_carlo_return_stats(paths, initial_value)
boot_ret = monte_carlo_return_stats(bootstrap_paths, initial_value)

col_s1, col_s2 = st.columns(2)
with col_s1:
    st.markdown("**Parametric**")
    for k, v in param_stats.items():
        if "Probability" in k:
            st.metric(k, f"{v:.2%}", help="Fraction of simulated scenarios where this outcome occurred.")
        else:
            st.metric(k, f"${v:,.2f}")

with col_s2:
    st.markdown("**Bootstrap**")
    for k, v in boot_stats.items():
        if "Probability" in k:
            st.metric(k, f"{v:.2%}", help="Fraction of simulated scenarios where this outcome occurred.")
        else:
            st.metric(k, f"${v:,.2f}")

with st.expander("Return Statistics"):
    st.caption("Return-focused stats including VaR, CVaR, and average max drawdown across all simulated paths.")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown("**Parametric Returns**")
        for k, v in param_ret.items():
            if "Probability" in k:
                st.metric(k, f"{v:.2%}")
            else:
                st.metric(k, f"{v:.4f}")
    with col_r2:
        st.markdown("**Bootstrap Returns**")
        for k, v in boot_ret.items():
            if "Probability" in k:
                st.metric(k, f"{v:.2%}")
            else:
                st.metric(k, f"{v:.4f}")

with st.expander("Final Value Distribution"):
    st.caption("Histogram of ending portfolio values. Red dashed line = initial investment. "
               "More mass to the right of the line = higher chance of profit.")
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Parametric", "Bootstrap"))
    fig.add_trace(go.Histogram(x=paths[-1, :], nbinsx=100, name="Parametric", marker_color="#4c78a8", opacity=0.7), row=1, col=1)
    fig.add_trace(go.Histogram(x=bootstrap_paths[-1, :], nbinsx=100, name="Bootstrap", marker_color="#00d4aa", opacity=0.7), row=1, col=2)
    for i in [1, 2]:
        fig.add_vline(x=initial_value, line_dash="dash", line_color="red", row=1, col=i)
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

with st.expander("Compare Portfolios Under Stress"):
    st.subheader("Stress Comparison")
    st.caption("Define different allocations and see how they fare under Monte Carlo stress. "
               "Compare conservative vs aggressive approaches.")
    n_allocs = st.number_input("Allocations to compare", value=3, min_value=2, max_value=5)

    allocs = {}
    for i in range(n_allocs):
        with st.expander(f"Allocation {i + 1}", expanded=(i == 0)):
            name = st.text_input("Name", value=["Optimized", "Equal Weight", "Aggressive", "Growth", "Speculative"][i], key=f"mc_name_{i}")
            alloc_w = {}
            half = (len(tickers) + 1) // 2
            c1, c2 = st.columns(2)

            if i == 0 and rec_weights:
                for j, t in enumerate(tickers):
                    c = c1 if j < half else c2
                    with c:
                        alloc_w[t] = st.slider(f"{t} %", 0, 100, round(rec_weights.get(t, 0) * 100), key=f"mc_alloc_{i}_{t}") / 100
            else:
                for j, t in enumerate(tickers):
                    c = c1 if j < half else c2
                    with c:
                        alloc_w[t] = st.slider(f"{t} %", 0, 100, round(100 / len(tickers)), key=f"mc_alloc_{i}_{t}") / 100
            total_a = sum(alloc_w.values())
            if abs(total_a - 1.0) > 0.01:
                st.error(f"Weights sum to {total_a:.0%}")
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
        fig.update_layout(title="Monte Carlo Comparison", barmode="group", template="plotly_dark", height=500)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
render_next_button("Rolling Optimization", "6_Rolling_Optimization.py")
