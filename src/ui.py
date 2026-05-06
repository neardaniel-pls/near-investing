import streamlit as st
import plotly.graph_objects as go
from src.config import load_config


def init_shared_state():
    cfg = load_config()
    defaults = {
        "risk_free_rate": cfg.get("risk_free_rate", 4.0) / 100,
        "initial_investment": cfg.get("initial_investment", 10000),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def require_data():
    if "returns" not in st.session_state:
        st.markdown(
            '<div style="text-align:center; padding:80px 20px;">'
            '<h2>No Data Loaded</h2>'
            '<p style="color:#aaa; font-size:1.1em;">Head to <b>Overview</b> to fetch your portfolio data first.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("Go to Overview", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Overview.py")
        st.stop()


def render_workflow_stepper(current_step: int):
    steps = [
        ("Overview", "1_Overview"),
        ("Risk", "2_Risk_Metrics"),
        ("Backtest", "3_Backtest"),
        ("Optimize", "4_Optimization"),
        ("Monte Carlo", "5_Monte_Carlo"),
        ("Rolling", "6_Rolling_Optimization"),
    ]
    cols = st.columns(len(steps))
    for i, ((label, _), col) in enumerate(zip(steps, cols)):
        with col:
            if i + 1 == current_step:
                st.markdown(
                    f'<div style="text-align:center; padding:8px 4px; border-radius:8px; '
                    f'background:#00d4aa22; border:1px solid #00d4aa; color:#00d4aa; font-weight:bold; font-size:0.85em;">'
                    f'{i+1}. {label}</div>',
                    unsafe_allow_html=True,
                )
            elif i + 1 < current_step:
                st.markdown(
                    f'<div style="text-align:center; padding:8px 4px; border-radius:8px; '
                    f'background:#00d4aa11; border:1px solid #00d4aa55; color:#00d4aa99; font-size:0.85em;">'
                    f'{i+1}. {label}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div style="text-align:center; padding:8px 4px; border-radius:8px; '
                    f'background:#ffffff08; border:1px solid #ffffff22; color:#666; font-size:0.85em;">'
                    f'{i+1}. {label}</div>',
                    unsafe_allow_html=True,
                )


def render_next_button(next_page_label: str, next_page_file: str):
    col1, col2, col3 = st.columns([2, 1, 2])
    with col3:
        if st.button(f"{next_page_label} →", use_container_width=True, type="primary"):
            st.switch_page(f"pages/{next_page_file}")


def render_portfolio_info():
    tickers = st.session_state.get("tickers", [])
    if tickers:
        with st.expander("Current Portfolio", expanded=False):
            st.markdown("**Tickers:** " + ", ".join(tickers))
            prices = st.session_state.get("prices")
            if prices is not None and not prices.empty:
                st.markdown(f"**Date range:** {prices.index[0].strftime('%Y-%m-%d')} → {prices.index[-1].strftime('%Y-%m-%d')}")
                st.markdown(f"**Trading days:** {len(prices)}")


def render_weight_sliders(tickers: list, key_prefix: str, default_weights: dict | None = None):
    if default_weights is None:
        default_weights = {}

    st.markdown("**Allocation (%)**")
    auto_normalize = st.checkbox("Auto-normalize to 100%", value=True, key=f"{key_prefix}_auto",
                                 help="Automatically rescale all weights so they sum to 100%.")

    equal_val = round(100 / len(tickers))

    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        if st.button("Equal Weight", key=f"{key_prefix}_equal"):
            for t in tickers:
                st.session_state[f"{key_prefix}_{t}"] = equal_val
    with btn_col2:
        opt_weights = st.session_state.get("recommended_weights")
        opt_label = st.session_state.get("recommended_label", "")
        if opt_weights:
            if st.button(f"Use Optimized", key=f"{key_prefix}_useopt",
                         help=f"Load weights from: {opt_label}"):
                for t in tickers:
                    st.session_state[f"{key_prefix}_{t}"] = round(opt_weights.get(t, 0) * 100)
    with btn_col3:
        pass

    if opt_weights:
        st.caption(f"Optimized weights available: **{opt_label}** — click 'Use Optimized' above to load them.")

    weights = {}
    half = (len(tickers) + 1) // 2
    col1, col2 = st.columns(2)

    for i, t in enumerate(tickers):
        col = col1 if i < half else col2
        with col:
            default = default_weights.get(t, equal_val)
            w = st.slider(f"{t}", 0, 100, default, key=f"{key_prefix}_{t}")
            weights[t] = w / 100

    total = sum(weights.values())

    if auto_normalize and total > 0:
        weights = {k: v / total for k, v in weights.items()}
        total = 1.0

    if abs(total - 1.0) > 0.01:
        st.error(f"Weights sum to **{total:.0%}** — must be 100%")
    else:
        st.success(f"Total: **{total:.0%}**")

    with st.expander("Allocation Preview"):
        nonzero = {k: v for k, v in weights.items() if v > 0.001}
        if nonzero:
            fig = go.Figure(go.Pie(
                labels=list(nonzero.keys()),
                values=[v * 100 for v in nonzero.values()],
                hole=0.4,
                marker=dict(colors=_chart_colors(len(nonzero))),
            ))
            fig.update_layout(
                height=300, margin=dict(l=20, r=20, t=30, b=20),
                showlegend=True, legend=dict(orientation="h", y=-0.1),
            )
            st.plotly_chart(fig, use_container_width=True)

    return weights, abs(total - 1.0) <= 0.01


def _chart_colors(n: int) -> list:
    palette = [
        "#00d4aa", "#4c78a8", "#f58518", "#e45756", "#72b7b2",
        "#54a24b", "#eeca3b", "#b279a2", "#ff9da6", "#9d755d",
    ]
    return [palette[i % len(palette)] for i in range(n)]


def fmt_pct(val) -> str:
    if val is None:
        return "N/A"
    return f"{val:.2%}"


def save_recommended_weights(weights: dict, label: str):
    st.session_state["recommended_weights"] = weights
    st.session_state["recommended_label"] = label


def render_recommended_portfolio(prices, returns, tickers, rf):
    rec = st.session_state.get("recommended_weights")
    label = st.session_state.get("recommended_label", "")
    if not rec:
        return

    st.markdown("---")
    st.subheader("Recommended Portfolio")
    st.caption(f"Based on your last optimization: **{label}**. This portfolio will be auto-loaded in Monte Carlo and Backtest.")

    from src.portfolio import build_portfolio_returns
    from src.metrics import annualized_return, annualized_volatility, sharpe_ratio, max_drawdown

    port_ret = build_portfolio_returns(prices, rec)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ann. Return", f"{annualized_return(port_ret):.2%}")
    with col2:
        st.metric("Volatility", f"{annualized_volatility(port_ret):.2%}")
    with col3:
        st.metric("Sharpe", f"{sharpe_ratio(port_ret, rf=rf):.3f}")
    with col4:
        st.metric("Max Drawdown", f"{max_drawdown(port_ret):.2%}", delta_color="inverse")

    nonzero = {k: v for k, v in rec.items() if v > 0.001}
    col_alloc, col_chart = st.columns([1, 1])
    with col_alloc:
        for t, w in sorted(nonzero.items(), key=lambda x: -x[1]):
            bar_len = int(w * 30)
            st.markdown(f"**{t}**: {w:.2%} `{'█' * bar_len}`")
    with col_chart:
        if nonzero:
            fig = go.Figure(go.Pie(labels=list(nonzero.keys()), values=[v * 100 for v in nonzero.values()], hole=0.4))
            fig.update_layout(template="plotly_dark", height=250, margin=dict(l=10, r=10, t=10, b=10),
                              showlegend=True, legend=dict(orientation="h", y=-0.1))
            st.plotly_chart(fig, use_container_width=True)


def fmt_dec(val, decimals=4) -> str:
    if val is None:
        return "N/A"
    return f"{val:.{decimals}f}"


def fmt_currency(val) -> str:
    if val is None:
        return "N/A"
    return f"${val:,.2f}"
