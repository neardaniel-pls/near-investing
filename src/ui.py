import streamlit as st
from src.config import load_config, update_config
from src.styles import CHART_PALETTE, section_title


BEGINNER_LABELS = {
    "CAGR": "Avg Yearly Growth",
    "Sharpe Ratio": "Risk-Adjusted Score",
    "Sortino Ratio": "Downside Score",
    "Calmar Ratio": "Return vs Worst Loss",
    "Omega Ratio": "Win/Loss Ratio",
    "Annualized Volatility": "Price Swings",
    "Volatility": "Price Swings",
    "Max Drawdown": "Worst Loss",
    "Max DD": "Worst Loss",
    "CVaR (95%)": "Bad-Day Loss",
    "CVaR": "Bad-Day Loss",
    "Annualized Return": "Yearly Return",
    "Total Return": "Total Gain",
    "Treynor Ratio": "Market-Adjusted Score",
    "Information Ratio": "vs Benchmark Score",
    "Alpha": "Extra Return",
    "Beta": "Market Sensitivity",
    "Skewness": "Gain/Loss Balance",
    "Kurtosis": "Extreme Events",
    "Best Day": "Best Day",
    "Worst Day": "Worst Day",
    "Avg Daily Return": "Avg Daily Gain",
}

BEGINNER_DESCRIPTIONS = {
    "CAGR": "Your average yearly return if you reinvested all profits.",
    "Sharpe Ratio": "How much return you get for each unit of risk. Above 1.0 is good, above 2.0 is great.",
    "Max Drawdown": "The biggest drop from a peak. If -30%, you lost 30% from your highest point.",
    "Volatility": "How much prices swing around. Higher = more unpredictable.",
    "CVaR (95%)": "How much you'd typically lose on the worst 5% of days.",
    "Total Return": "Your total gain or loss from start to finish.",
    "Sortino Ratio": "Like the Sharpe score but only counts downside swings. Better for crypto/asymmetric returns.",
    "Alpha": "Return above what the market model predicts. Positive = you beat expectations.",
    "Beta": "How much this asset moves with the market. Above 1 = more volatile than the market.",
}

ADVANCED_DESCRIPTIONS = {
    "CAGR": "Compound Annual Growth Rate — the annualized return assuming compounding.",
    "Sharpe Ratio": "(Return - Risk-free rate) / Volatility. Above 1.0 is good, above 2.0 is excellent.",
    "Max Drawdown": "Largest peak-to-trough decline.",
    "Volatility": "Annualized standard deviation of daily returns.",
    "CVaR (95%)": "Expected loss in the worst 5% of days. More sensitive to tail risk than VaR.",
    "Total Return": "Cumulative return from start to end date.",
    "Sortino Ratio": "Like Sharpe but only penalizes downside volatility.",
    "Alpha": "Return above CAPM prediction. Positive = outperformed expectations.",
    "Beta": "Covariance with benchmark / benchmark variance. >1 = more volatile than benchmark.",
}

PAGE_ICONS = {
    "Dashboard": "\U0001f3e0",
    "Risk": "\u26a1",
    "Optimize": "\u2699\ufe0f",
    "Backtest": "\U0001f3af",
    "Simulate": "\U0001f3b2",
}

PAGE_SUBTITLES = {
    "Dashboard": "Your portfolio at a glance",
    "Risk": "Deep dive into risk/return metrics for each asset",
    "Optimize": "Find the optimal asset allocation for your goals",
    "Backtest": "Test allocations with buy-and-hold or rebalancing",
    "Simulate": "Monte Carlo and walk-forward simulations",
}

PAGE_SUBTITLES_BEGINNER = {
    "Dashboard": "See how your investments are performing",
    "Risk": "Understand how risky each investment is",
    "Optimize": "Find the best mix of investments for your goals",
    "Backtest": "Test how your portfolio would have done in the past",
    "Simulate": "Simulate thousands of possible futures",
}


def get_mode() -> str:
    return st.session_state.get("ui_mode", "beginner")


def is_beginner() -> bool:
    return get_mode() == "beginner"


def label(metric_name: str) -> str:
    if is_beginner():
        return BEGINNER_LABELS.get(metric_name, metric_name)
    return metric_name


def metric_help(metric_name: str) -> str:
    if is_beginner():
        return BEGINNER_DESCRIPTIONS.get(metric_name, "")
    return ADVANCED_DESCRIPTIONS.get(metric_name, "")


def render_mode_toggle():
    cfg = load_config()
    if "ui_mode" not in st.session_state:
        st.session_state["ui_mode"] = cfg.get("ui_mode", "beginner")

    current = st.session_state["ui_mode"]

    if current == "beginner":
        btn_label = "\U0001f31f Beginner"
        btn_help = "Switch to Advanced mode to see technical financial metrics"
    else:
        btn_label = "\U0001f52c Advanced"
        btn_help = "Switch to Beginner mode for simplified labels"

    if st.button(btn_label, help=btn_help, use_container_width=True, key="_mode_toggle"):
        new_mode = "advanced" if current == "beginner" else "beginner"
        st.session_state["ui_mode"] = new_mode
        update_config(ui_mode=new_mode)
        st.rerun()


def init_shared_state():
    cfg = load_config()
    defaults = {
        "risk_free_rate": cfg.get("risk_free_rate", 4.0) / 100,
        "initial_investment": cfg.get("initial_investment", 10000),
        "ui_mode": cfg.get("ui_mode", "beginner"),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def require_data():
    if "returns" not in st.session_state:
        if is_beginner():
            msg = "You need to load your portfolio data first."
            btn_text = "Go to Home"
        else:
            msg = "No data loaded. Go to the home page to fetch portfolio data."
            btn_text = "Go to Home"

        st.markdown(
            f'<div style="text-align:center; padding:80px 20px;">'
            f'<h2>No Data Loaded</h2>'
            f'<p style="color:#aaa; font-size:1.1em;">{msg}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button(btn_text, use_container_width=True, type="primary"):
            st.switch_page("app.py")
        st.stop()


PAGES = [
    ("Dashboard", "1_Dashboard"),
    ("Risk", "2_Risk"),
    ("Optimize", "3_Optimize"),
    ("Backtest", "4_Backtest"),
    ("Simulate", "5_Simulate"),
]


def render_nav_bar(current_page: str):
    has_data = "prices" in st.session_state
    items_html = ""
    for page_name, page_file in PAGES:
        icon = PAGE_ICONS.get(page_name, "")
        is_current = page_name == current_page

        if is_current:
            items_html += (
                f'<div class="nav-item active">'
                f'{icon} {page_name}</div>'
            )
        else:
            border_c = "#00d4aa55" if has_data else "#ffffff22"
            bg_c = "#00d4aa11" if has_data else "#ffffff08"
            text_c = "#00d4aa99" if has_data else "#666"
            items_html += (
                f'<div class="nav-item" style="background:{bg_c};border-color:{border_c};color:{text_c};">'
                f'{icon} {page_name}</div>'
            )

    st.markdown(
        f'<div class="nav-bar">{items_html}</div>',
        unsafe_allow_html=True,
    )


def render_workflow_stepper(current_step: int):
    page_names = [p[0] for p in PAGES]
    if 1 <= current_step <= len(page_names):
        current_page = page_names[current_step - 1]
    else:
        current_page = "Overview"
    render_nav_bar(current_page)


def render_page_header(page_name: str):
    icon = PAGE_ICONS.get(page_name, "")
    subtitle = PAGE_SUBTITLES.get(page_name, "")
    if is_beginner() and page_name in PAGE_SUBTITLES_BEGINNER:
        subtitle = PAGE_SUBTITLES_BEGINNER[page_name]

    st.markdown(
        f'<div class="page-header">'
        f'<div><span class="page-icon">{icon}</span></div>'
        f'<div>'
        f'<div class="page-title">{page_name}</div>'
        f'<div class="page-subtitle">{subtitle}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_next_button(next_page_label: str, next_page_file: str):
    col1, col2, col3 = st.columns([2, 1, 2])
    with col3:
        icon = PAGE_ICONS.get(next_page_label, "")
        if st.button(f"{icon} {next_page_label} \u2192", use_container_width=True, type="primary"):
            st.switch_page(f"pages/{next_page_file}")


def render_portfolio_info():
    tickers = st.session_state.get("tickers", [])
    if tickers:
        with st.expander("\U0001f4cb Current Portfolio", expanded=False):
            st.markdown("**Tickers:** " + ", ".join(tickers))
            prices = st.session_state.get("prices")
            if prices is not None and not prices.empty:
                st.markdown(f"**Date range:** {prices.index[0].strftime('%Y-%m-%d')} \u2192 {prices.index[-1].strftime('%Y-%m-%d')}")
                st.markdown(f"**Trading days:** {len(prices)}")


def render_weight_sliders(tickers: list, key_prefix: str, default_weights: dict | None = None):
    if default_weights is None:
        default_weights = {}

    alloc_label = "Allocation (%)" if not is_beginner() else "How much to invest (%)"
    st.markdown(f"**{alloc_label}**")
    auto_normalize = st.checkbox(
        "Auto-normalize to 100%" if not is_beginner() else "Auto-balance weights to 100%",
        value=True, key=f"{key_prefix}_auto",
        help="Automatically rescale all weights so they sum to 100%." if not is_beginner()
        else "Make all your percentages add up to 100% automatically.",
    )

    equal_val = round(100 / len(tickers))

    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        if st.button("Equal Weight" if not is_beginner() else "Split Evenly", key=f"{key_prefix}_equal"):
            for t in tickers:
                st.session_state[f"{key_prefix}_{t}"] = equal_val
    with btn_col2:
        opt_weights = st.session_state.get("recommended_weights")
        opt_label = st.session_state.get("recommended_label", "")
        if opt_weights:
            btn_text = "Use Optimized" if not is_beginner() else "Use Best Mix"
            if st.button(btn_text, key=f"{key_prefix}_useopt",
                         help=f"Load weights from: {opt_label}"):
                for t in tickers:
                    st.session_state[f"{key_prefix}_{t}"] = round(opt_weights.get(t, 0) * 100)
    with btn_col3:
        pass

    if opt_weights:
        st.caption(f"\u2705 Optimized weights available: **{opt_label}**")

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

    if total == 0:
        st.error("All weights are 0% \u2014 at least one asset must have a non-zero allocation.")
        return weights, False

    if auto_normalize and total > 0:
        weights = {k: v / total for k, v in weights.items()}
        total = 1.0

    if abs(total - 1.0) > 0.01:
        st.error(f"Weights sum to **{total:.0%}** \u2014 must be 100%")
    else:
        st.success(f"Total: **{total:.0%}**")

    with st.expander("\U0001f4ca Allocation Preview"):
        nonzero = {k: v for k, v in weights.items() if v > 0.001}
        if nonzero:
            from src.charts import make_pie_chart
            fig = make_pie_chart(
                labels=list(nonzero.keys()),
                values=[v * 100 for v in nonzero.values()],
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)

    return weights, abs(total - 1.0) <= 0.01


def fmt_pct(val) -> str:
    if val is None:
        return "N/A"
    return f"{val:.2%}"


def fmt_dec(val, decimals=4) -> str:
    if val is None:
        return "N/A"
    return f"{val:.{decimals}f}"


def fmt_currency(val) -> str:
    if val is None:
        return "N/A"
    return f"${val:,.2f}"


def save_recommended_weights(weights: dict, label: str):
    st.session_state["recommended_weights"] = weights
    st.session_state["recommended_label"] = label


def render_recommended_portfolio(prices, returns, tickers, rf):
    rec = st.session_state.get("recommended_weights")
    rec_label = st.session_state.get("recommended_label", "")
    if not rec:
        return

    st.markdown("---")
    section_title("\U0001f3c6 Recommended Portfolio" if not is_beginner() else "\u2b50 Best Portfolio Mix")
    if is_beginner():
        st.caption(f"Based on your last optimization: **{rec_label}**. These weights are used in simulations.")
    else:
        st.caption(f"Based on your last optimization: **{rec_label}**. Auto-loaded in Monte Carlo and Backtest.")

    from src.portfolio import build_portfolio_returns
    from src.metrics import annualized_return, annualized_volatility, sharpe_ratio, max_drawdown

    port_ret = build_portfolio_returns(prices, rec)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label("Annualized Return"), f"{annualized_return(port_ret):.2%}")
    with col2:
        st.metric(label("Volatility"), f"{annualized_volatility(port_ret):.2%}")
    with col3:
        st.metric(label("Sharpe Ratio"), f"{sharpe_ratio(port_ret, rf=rf):.3f}")
    with col4:
        st.metric(label("Max Drawdown"), f"{max_drawdown(port_ret):.2%}", delta_color="inverse")

    nonzero = {k: v for k, v in rec.items() if v > 0.001}
    col_alloc, col_chart = st.columns([1, 1])
    with col_alloc:
        for t, w in sorted(nonzero.items(), key=lambda x: -x[1]):
            bar_len = int(w * 30)
            st.markdown(f"**{t}**: {w:.2%} `{'\u2588' * bar_len}`")
    with col_chart:
        if nonzero:
            from src.charts import make_pie_chart
            fig = make_pie_chart(
                labels=list(nonzero.keys()),
                values=[v * 100 for v in nonzero.values()],
                height=280,
            )
            st.plotly_chart(fig, use_container_width=True)


def load_sample_portfolio():
    tickers = ["AAPL", "MSFT", "VWCE.MI", "AGGH.AS", "BTC-USD", "^GSPC"]
    start = "2020-01-01"
    import pandas as pd
    end = str((pd.Timestamp.now().normalize() - pd.Timedelta(days=1)).date())

    from src.data import fetch_prices, compute_returns, fetch_ticker_names

    with st.spinner("Loading sample portfolio..."):
        prices = fetch_prices(tickers, start=start, end=end, use_cache=True)
    if prices.empty:
        st.error("Could not load sample data. Check your internet connection.")
        return False
    returns = compute_returns(prices)
    with st.spinner("Resolving ticker names..."):
        ticker_names = fetch_ticker_names(tickers)

    st.session_state["prices"] = prices
    st.session_state["returns"] = returns
    st.session_state["tickers"] = tickers
    st.session_state["ticker_names"] = ticker_names
    st.toast(f"Loaded {len(prices)} trading days for {len(tickers)} assets", icon="\u2705")
    return True
