import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.portfolio import build_portfolio_returns, equity_curve
from src.monte_carlo import (
    simulate_portfolio_monte_carlo,
    simulate_historical_bootstrap,
    monte_carlo_statistics,
    monte_carlo_return_stats,
)
from src.rolling import (
    rolling_optimize, walk_forward_test_returns,
    rolling_weights_over_time, compare_rolling_strategies,
)
from src.metrics import metrics_table, sharpe_ratio, annualized_return
from src.optimization import OPTIMIZATION_TARGETS
from src.ui import (
    init_shared_state, require_data, render_workflow_stepper,
    render_portfolio_info, render_weight_sliders,
    save_recommended_weights, render_recommended_portfolio,
    render_page_header, render_recommended_sidebar_widget,
    is_beginner, label,
)
from src.styles import inject_global_styles, divider, section_title
from src.charts import apply_theme, chart_colors, make_bar_chart, format_dataframe_styler

st.set_page_config(page_title="Simulate", layout="wide")
inject_global_styles()
init_shared_state()
render_workflow_stepper(5)
render_page_header("Simulate")
require_data()

prices = st.session_state["prices"]
returns = st.session_state["returns"]
tickers = st.session_state.get("tickers", [])
initial_value = st.session_state.get("initial_investment", 10000)
rf = st.session_state.get("risk_free_rate", 0.04)

rec_weights = st.session_state.get("recommended_weights")
rec_label = st.session_state.get("recommended_label", "")

tab_labels = ["Monte Carlo", "Walk-Forward"]
if is_beginner():
    tab_labels = ["Future Scenarios", "Time-Period Test"]
tab_mc, tab_rolling = st.tabs(tab_labels)

# ═══════════════════════════════════════════════════════════════════
# TAB 1: MONTE CARLO
# ═══════════════════════════════════════════════════════════════════

with tab_mc:
    with st.sidebar:
        render_recommended_sidebar_widget()
        st.markdown("#### Monte Carlo Weights")
        if rec_weights:
            st.success(f"Optimized: **{rec_label}**")
            if is_beginner():
                st.caption("Weights auto-loaded from your last optimization.")
            else:
                st.caption("Weights auto-loaded from Optimization.")
        else:
            st.info("No optimization run yet. Set weights manually or run Optimize first.")

        default_w = {t: v * 100 for t, v in rec_weights.items()} if rec_weights else None
        weights, weights_valid = render_weight_sliders(
            tickers, key_prefix="mc", default_weights=default_w,
        )

    if not weights_valid:
        st.warning("Set valid weights in the sidebar first.")
        st.stop()

    with st.expander("\u2753 What does this simulation do?" if is_beginner() else "\u2753 What is Monte Carlo simulation?"):
        if is_beginner():
            st.markdown("""
            **Monte Carlo** generates thousands of possible futures to stress-test your portfolio.

            - **Historical (realistic)** \u2014 randomly picks real past daily changes to build futures. Captures actual crashes and rallies. **Recommended.**
            - **Statistical (theoretical)** \u2014 assumes returns follow a smooth bell curve. Quick but may underestimate extreme events.

            **Key outputs:**
            - **Expected Value** \u2014 what your portfolio is most likely worth after the simulation period.
            - **95% Range** \u2014 "There's a 95% chance your portfolio lands between these two values."
            - **Probability of Loss** \u2014 % chance you end up with less than you started.
            """)
        else:
            st.markdown("""
            **Monte Carlo** generates thousands of possible future scenarios to stress-test your portfolio.

            - **Historical Bootstrap** \u2014 randomly picks actual past daily returns to build scenarios. Captures fat tails and real-world patterns. **Recommended for realism.**
            - **Parametric** \u2014 assumes returns follow a normal distribution with historical mean and volatility. Good for quick estimates but underestimates extreme events.

            **Key outputs:**
            - **VaR (Value at Risk)** \u2014 portfolio value at the 5th percentile. 95% chance of having at least this much.
            - **CVaR** \u2014 average outcome in the worst 5% of scenarios.
            - **Probability of Loss** \u2014 % of scenarios where you end up with less than you started.
            """)

    # --- INLINE SETTINGS ---
    if rec_weights:
        st.caption(f"Simulating with weights from: **{rec_label}**")

    settings_col1, settings_col2, settings_col3, settings_col4 = st.columns([2, 2, 2, 1])
    with settings_col1:
        period_opts = {
            "3 months (63 days)": 63, "6 months (126 days)": 126,
            "1 year (252 days)": 252, "2 years (504 days)": 504,
            "5 years (1260 days)": 1260,
        }
        period_label = "Simulation period" if not is_beginner() else "How far into the future?"
        period_choice = st.selectbox(period_label, list(period_opts.keys()), index=2, key="mc_period_select")
        n_days = period_opts[period_choice]

    with settings_col2:
        sims_label = "Number of simulations" if not is_beginner() else "How many futures to simulate?"
        n_sims = st.selectbox(sims_label, [1000, 5000, 10000, 50000], index=2,
                              help="More = more accurate but slower.")

    with settings_col3:
        method_label = "Simulation method" if not is_beginner() else "How to generate futures?"
        method_options = ["Historical (realistic)", "Statistical (theoretical)"] if is_beginner() \
            else ["Historical Bootstrap", "Parametric"]
        method_choice = st.selectbox(method_label, method_options, index=0)

    with settings_col4:
        seed = st.number_input("Seed", value=42, help="Fixed seed = reproducible results.")

    # --- RUN SIMULATIONS ---
    use_historical = "Historical" in method_choice

    portfolio_rets = build_portfolio_returns(prices, weights)

    with st.spinner("Running simulations..."):
        bootstrap_paths = simulate_historical_bootstrap(
            portfolio_rets, n_simulations=n_sims, n_days=n_days,
            initial_value=initial_value, random_seed=seed,
        )
        if use_historical:
            main_paths = bootstrap_paths
        else:
            main_paths = simulate_portfolio_monte_carlo(
                portfolio_rets, n_simulations=n_sims, n_days=n_days,
                initial_value=initial_value, random_seed=seed,
            )

    # --- SUMMARY CARD ---
    main_stats = monte_carlo_statistics(main_paths)
    main_ret_stats = monte_carlo_return_stats(main_paths, initial_value)

    section_title("\U0001f4cb Summary" if not is_beginner() else "\U0001f4cb Your Simulation Results")

    mean_val = main_stats["Mean Final Value"]
    p5_val = main_stats["Worst Case (5%)"]
    p95_val = main_stats["Best Case (5%)"]
    prob_profit = main_stats["Probability of Profit"]
    prob_big_loss = main_stats["Probability of >50% Loss"]
    mean_return = main_ret_stats["Mean Return"]

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(
            "Expected Value" if not is_beginner() else "Most Likely Outcome",
            f"${mean_val:,.0f}",
            delta=f"{mean_return:+.1%} return",
        )
    with kpi2:
        st.metric(
            "95% Range" if not is_beginner() else "Likely Range (95%)",
            f"${p5_val:,.0f} \u2014 ${p95_val:,.0f}",
        )
    with kpi3:
        prob_loss = 1 - prob_profit
        st.metric(
            "Probability of Loss" if not is_beginner() else "Chance of Losing Money",
            f"{prob_loss:.1%}",
            delta_color="inverse",
        )
    with kpi4:
        st.metric(
            "Probability of >50% Loss" if not is_beginner() else "Chance of Losing Half",
            f"{prob_big_loss:.1%}",
            delta_color="inverse",
        )

    # --- MAIN CHART ---
    divider()
    section_title(f"\U0001f52c Simulated Paths ({method_choice})")

    n_show = min(200, main_paths.shape[1])
    fig = go.Figure()
    path_color = "rgba(100,200,100,0.08)" if use_historical else "rgba(100,100,255,0.08)"
    for i in range(n_show):
        fig.add_trace(go.Scatter(
            y=main_paths[:, i], mode="lines",
            line=dict(width=0.5, color=path_color),
            showlegend=False,
        ))
    mean_path = np.mean(main_paths, axis=1)
    p5 = np.percentile(main_paths, 5, axis=1)
    p95 = np.percentile(main_paths, 95, axis=1)
    fig.add_trace(go.Scatter(y=p95, mode="lines", name="Best 5%", line=dict(width=1, color="green", dash="dash")))
    fig.add_trace(go.Scatter(y=mean_path, mode="lines", name="Average", line=dict(width=3, color="#00d4aa")))
    fig.add_trace(go.Scatter(y=p5, mode="lines", name="Worst 5%", line=dict(width=1, color="red", dash="dash")))
    fig.add_hline(y=initial_value, line_dash="dash", line_color="gray")
    fig.update_layout(yaxis_title="Value ($)", xaxis_title="Trading Days")
    apply_theme(fig, height=500)
    st.plotly_chart(fig, use_container_width=True, key="mc_main_chart")

    # --- DETAILED STATS IN EXPANDERS ---
    with st.expander("\U0001f4ca Detailed Statistics"):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("**Value Statistics**")
            for k in ["Median Final Value", "Std Final Value",
                       f"VaR ({0.95:.0%})", f"CVaR ({0.95:.0%})",
                       "Best Case (5%)", "Worst Case (5%)",
                       "Min Final Value", "Max Final Value"]:
                if k in main_stats:
                    v = main_stats[k]
                    if "Probability" in k:
                        st.metric(k, f"{v:.2%}")
                    else:
                        st.metric(k, f"${v:,.0f}")

        with col_s2:
            st.markdown("**Return Statistics**")
            for k, v in main_ret_stats.items():
                if "Probability" in k:
                    st.metric(k, f"{v:.2%}")
                elif "Drawdown" in k:
                    st.metric(k, f"{v:.2%}")
                else:
                    st.metric(k, f"{v:.4f}")

    with st.expander("\U0001f4ca Final Value Distribution"):
        if is_beginner():
            st.caption("Histogram of ending values. Red line = starting amount. More area to the right = higher chance of profit.")
        else:
            st.caption("Histogram of ending portfolio values across all simulated paths. Red dashed line = initial investment.")
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=main_paths[-1, :], nbinsx=100,
            marker_color="#00d4aa", opacity=0.7,
        ))
        fig.add_vline(x=initial_value, line_dash="dash", line_color="red")
        fig.add_vline(x=mean_val, line_dash="solid", line_color="#00d4aa",
                      annotation_text=f"Mean: ${mean_val:,.0f}")
        fig.update_layout(xaxis_title="Final Value ($)", yaxis_title="Count")
        apply_theme(fig, height=400)
        st.plotly_chart(fig, use_container_width=True, key="mc_distribution")

    with st.expander("\U0001f4ca Compare Different Methods"):
        if is_beginner():
            st.caption("Side-by-side comparison of both simulation methods.")
        else:
            st.caption("Parametric (theoretical normal distribution) vs Historical Bootstrap (real past returns).")

        boot_stats = monte_carlo_statistics(bootstrap_paths)
        if not use_historical:
            boot_ret = monte_carlo_return_stats(bootstrap_paths, initial_value)
        else:
            boot_ret = main_ret_stats

        compare_metrics = ["Mean Final Value", "Worst Case (5%)", "Best Case (5%)",
                          "Probability of Profit", "Probability of >50% Loss"]
        rows = []
        for k in compare_metrics:
            v_main = main_stats.get(k, 0)
            v_boot = boot_stats.get(k, 0)
            if "Probability" in k:
                rows.append({"Metric": k, "Current Method": f"{v_main:.2%}", "Historical Bootstrap": f"{v_boot:.2%}"})
            else:
                rows.append({"Metric": k, "Current Method": f"${v_main:,.0f}", "Historical Bootstrap": f"${v_boot:,.0f}"})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with st.expander("\U0001f3d7 Compare Allocations Under Stress"):
        if is_beginner():
            st.caption("Define different investment mixes and see how they handle stress.")
        else:
            st.caption("Define different allocations and see how they fare under Monte Carlo stress.")
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
            fig = make_bar_chart(
                categories=list(results.keys()),
                values_dict={m: [results[k][m] for k in results] for m in metrics_to_plot},
                height=500,
            )
            st.plotly_chart(fig, use_container_width=True, key="stress_comparison")

# ═══════════════════════════════════════════════════════════════════
# TAB 2: WALK-FORWARD
# ═══════════════════════════════════════════════════════════════════

with tab_rolling:
    with st.sidebar:
        render_recommended_sidebar_widget()
        st.markdown("#### Walk-Forward Settings")
        target_help = ("The strategy to use in each rolling window." if not is_beginner()
                       else "The optimization method to use in each time window.")
        target = st.selectbox("Optimization target", OPTIMIZATION_TARGETS + ["hrp"], help=target_help)
        train_help = ("How much historical data to use for optimization. 252 = ~1 year." if not is_beginner()
                      else "How much past data to learn from. 252 days \u2248 1 year.")
        train_window = st.selectbox("Training window (days)", [126, 252, 504, 756], index=1, help=train_help)
        test_help = ("How far forward to test the optimized weights. 21 = ~1 month." if not is_beginner()
                     else "How far ahead to test. 21 days \u2248 1 month.")
        test_window = st.selectbox("Test window (days)", [5, 21, 42, 63], index=1, help=test_help)
        step_help = ("How often to re-optimize. 21 = monthly rebalance." if not is_beginner()
                     else "How often to recalculate. 21 days \u2248 monthly.")
        step = st.selectbox("Rebalance step (days)", [5, 21, 42, 63], index=1, help=step_help)

        run_label = "Run Rolling Optimization" if not is_beginner() else "Start Rolling Test"
        run_btn = st.button(run_label, type="primary", use_container_width=True)

    with st.expander("\u2753 What is rolling optimization?" if not is_beginner() else "\u2753 How does walk-forward work?"):
        if is_beginner():
            st.markdown("""
            **Walk-forward** tests your strategy as if you were using it in real-time:

            1. **Learn** \u2014 find the best mix using past data (e.g. the last year)
            2. **Test** \u2014 apply that mix to the next period (e.g. the next month)
            3. **Repeat** \u2014 move forward and do it again

            This is a more realistic test than a single backtest.

            - **Past-Data Score** \u2014 how good it looked on past data
            - **Actual Return** \u2014 what actually happened in the next period
            - **Walk-Forward Curve** \u2014 cumulative performance if you followed this strategy
            """)
        else:
            st.markdown("""
            **Rolling (walk-forward) optimization** tests how your strategy would perform in real-time by repeatedly:

            1. **Training** \u2014 optimizing weights on a past window (e.g. the last 252 trading days)
            2. **Testing** \u2014 applying those weights to the next period (e.g. the next 21 days)
            3. **Rolling forward** \u2014 moving the window ahead and repeating

            - **Train Sharpe** \u2014 how good the optimization looked on past data (in-sample)
            - **Test Return** \u2014 what actually happened in the out-of-sample period
            - **Walk-Forward Curve** \u2014 cumulative performance if you had followed this strategy
            - **Weights Over Time** \u2014 how the optimizer's allocation changed across market regimes
            """)

    if run_btn or "rolling_results" in st.session_state:
        if run_btn:
            with st.spinner(f"Running rolling optimization ({target})..."):
                results = rolling_optimize(
                    prices, target=target, train_window=train_window,
                    test_window=test_window, step=step, risk_free_rate=rf,
                )
                st.session_state["rolling_results"] = results
                st.session_state["rolling_target"] = target
                st.toast(f"Rolling optimization complete: {len(results)} windows", icon="\u2705")

        results = st.session_state["rolling_results"]
        target_name = st.session_state.get("rolling_target", target)

        # --- KPI SUMMARY ---
        section_title(f"Results: {target_name} ({len(results)} windows)")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label("Avg Train Sharpe") if not is_beginner() else "Avg Past-Data Score",
                      f"{results['train_sharpe'].mean():.3f}")
        with col2:
            st.metric(label("Avg Test Return") if not is_beginner() else "Avg Actual Return",
                      f"{results['test_return'].mean():.2%}")
        with col3:
            st.metric(label("Test Win Rate") if not is_beginner() else "% of Profitable Periods",
                      f"{(results['test_return'] > 0).mean():.1%}")

        # --- WEIGHTS OVER TIME ---
        section_title("\U0001f4ca Weights Over Time")
        if is_beginner():
            st.caption("How your portfolio mix changed over time.")
        else:
            st.caption("How the optimizer's allocation changed over time. Large swings suggest sensitivity to the data window.")
        weights_df = rolling_weights_over_time(results)
        fig = go.Figure()
        colors = chart_colors(len(weights_df.columns))
        for i, col in enumerate(weights_df.columns):
            fig.add_trace(go.Scatter(
                x=weights_df.index, y=weights_df[col] * 100,
                name=col, mode="lines", stackgroup="one",
                line=dict(color=colors[i]),
            ))
        fig.update_layout(yaxis_title="Weight %", xaxis_title="Date")
        apply_theme(fig, height=500)
        st.plotly_chart(fig, use_container_width=True, key="wf_weights")

        # --- WALK-FORWARD EQUITY CURVE ---
        wf_returns = walk_forward_test_returns(results, prices)
        if len(wf_returns) > 0:
            divider()
            section_title("\U0001f4c8 Walk-Forward Equity Curve")
            if is_beginner():
                st.caption("Cumulative performance if you followed this strategy vs equal-weight.")
            else:
                st.caption("Cumulative performance: rolling strategy vs static equal-weight benchmark.")
            equal_w = {t: 1.0 / len(tickers) for t in tickers}
            equal_ret = build_portfolio_returns(prices, equal_w)
            aligned_equal = equal_ret.reindex(wf_returns.index).dropna()
            aligned_wf = wf_returns.reindex(aligned_equal.index).dropna()

            curves = pd.DataFrame({
                f"Walk-Forward ({target_name})": equity_curve(aligned_wf, 10000),
                "Equal Weight": equity_curve(aligned_equal, 10000),
            })
            fig = go.Figure()
            colors = chart_colors(len(curves.columns))
            for i, col in enumerate(curves.columns):
                fig.add_trace(go.Scatter(x=curves.index, y=curves[col], name=col, mode="lines",
                                         line=dict(color=colors[i])))
            fig.update_layout(yaxis_title="Value ($)", xaxis_title="Date")
            apply_theme(fig, height=500)
            st.plotly_chart(fig, use_container_width=True, key="wf_equity")

            comp = {f"Walk-Forward ({target_name})": aligned_wf, "Equal Weight": aligned_equal}
            table = metrics_table(comp, rf=rf)
            styled = format_dataframe_styler(table)
            st.dataframe(styled, use_container_width=True)

        # --- TRAIN VS TEST ---
        with st.expander("\U0001f4c8 Train vs Test Performance"):
            if is_beginner():
                st.caption("Top: score on past data. Bottom: actual return. Big gaps suggest overfitting.")
            else:
                st.caption("Top: in-sample Sharpe. Bottom: out-of-sample return. Big gaps suggest overfitting.")
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                subplot_titles=("Past-Data Score" if is_beginner() else "Train Sharpe (In-Sample)",
                                                "Actual Return %" if is_beginner() else "Test Return (Out-of-Sample)"),
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
            fig.update_layout()
            apply_theme(fig, height=700)
            st.plotly_chart(fig, use_container_width=True, key="wf_train_test")

    else:
        info_msg = ("Configure settings in the sidebar and click **Run Rolling Optimization**."
                    if not is_beginner()
                    else "Set your preferences in the sidebar and click **Start Rolling Test**.")
        st.info(info_msg)

    # --- MULTI-STRATEGY COMPARISON (expander) ---
    with st.expander("\U0001f3d7 Compare Multiple Strategies"):
        if is_beginner():
            st.caption("Run multiple strategies side by side to see which performed best.")
        else:
            st.caption("Run multiple optimization strategies in walk-forward mode and compare which performed best out-of-sample.")

        compare_targets = st.multiselect(
            "Strategies to compare",
            OPTIMIZATION_TARGETS + ["hrp"],
            default=["max_sharpe", "min_volatility", "hrp"],
            help="Run multiple strategies and compare their walk-forward performance.",
            key="wf_compare_targets",
        )
        run_compare_btn = st.button("Compare Strategies", type="primary", key="wf_compare_btn")

        if run_compare_btn and compare_targets:
            with st.spinner(f"Comparing {len(compare_targets)} strategies..."):
                all_rolling = compare_rolling_strategies(
                    prices, targets=compare_targets, train_window=train_window,
                    test_window=test_window, step=step, risk_free_rate=rf,
                )
                st.session_state["compare_results"] = all_rolling
                st.toast("Strategy comparison complete!", icon="\u2705")

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

            rank_label = "Rank by" if not is_beginner() else "Rank by"
            rank_metric = st.selectbox(rank_label, [
                "WF Sharpe", "WF Ann. Return (%)", "WF Total Return (%)",
                "Avg Test Return (%)", "Test Win Rate (%)", "Avg Train Sharpe",
            ], index=0, key="rolling_rank_metric")

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

            st.success(f"\U0001f3c6 **Best: {best_name}** \u2014 {rank_metric}: {best_val:.3f}")
            if is_beginner():
                st.caption("This strategy's latest weights have been saved for use in simulations.")
            else:
                st.caption("This strategy's latest optimized weights have been saved as the recommended portfolio.")

            fig = go.Figure()
            bar_colors = []
            for i, (name, val) in enumerate(ranked.items()):
                if i == 0:
                    bar_colors.append("rgba(0,212,170,0.9)")
                elif i == 1:
                    bar_colors.append("rgba(0,212,170,0.5)")
                elif i == 2:
                    bar_colors.append("rgba(0,212,170,0.3)")
                else:
                    bar_colors.append("rgba(100,100,130,0.3)")
            fig.add_trace(go.Bar(
                y=ranked.index[::-1],
                x=ranked.values[::-1],
                orientation="h",
                marker_color=bar_colors[::-1],
                text=[f"{v:.3f}" for v in ranked.values[::-1]],
                textposition="outside",
            ))
            fig.update_layout(
                xaxis_title=rank_metric,
                margin=dict(l=160, r=80, t=20, b=40),
            )
            apply_theme(fig, height=max(250, len(ranked) * 36 + 80))
            st.plotly_chart(fig, use_container_width=True, key="wf_ranking_bar")

            divider()
            styled = format_dataframe_styler(summary_df)
            st.dataframe(styled, use_container_width=True)

            metrics_to_plot = ["Avg Train Sharpe", "Avg Test Return (%)", "Test Win Rate (%)"]
            available = [m for m in metrics_to_plot if m in summary_df.index]
            if available:
                fig = make_bar_chart(
                    categories=list(summary.keys()),
                    values_dict={m: [summary[k][m] for k in summary] for m in available},
                    height=400,
                )
                st.plotly_chart(fig, use_container_width=True, key="wf_compare_bars")

            if best_name and len(all_rolling[best_name]) > 0:
                with st.expander(f"\U0001f4ca Weights Over Time \u2014 {best_name} (Best)"):
                    best_weights_df = rolling_weights_over_time(all_rolling[best_name])
                    fig = go.Figure()
                    colors = chart_colors(len(best_weights_df.columns))
                    for i, col in enumerate(best_weights_df.columns):
                        fig.add_trace(go.Scatter(
                            x=best_weights_df.index, y=best_weights_df[col] * 100,
                            name=col, mode="lines", stackgroup="one",
                            line=dict(color=colors[i]),
                        ))
                    fig.update_layout(yaxis_title="Weight %", xaxis_title="Date")
                    apply_theme(fig, height=500)
                    st.plotly_chart(fig, use_container_width=True, key="wf_best_weights")

divider()
render_recommended_portfolio(prices, returns, tickers, rf)
