import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui import (
    init_shared_state, render_workflow_stepper,
    render_next_button, render_page_header,
    render_recommendation_banner, require_data,
    is_beginner, label,
)
from src.metrics import annualized_return, annualized_volatility, sharpe_ratio, max_drawdown, cagr
from src.portfolio import build_portfolio_returns
from src.styles import inject_global_styles, divider, section_title
from src.charts import apply_theme, chart_colors, make_heatmap, format_dataframe_styler
from src.export import render_export_section

st.set_page_config(page_title="Dashboard", layout="wide")
inject_global_styles()
init_shared_state()
render_workflow_stepper(1)
render_page_header("Dashboard")
require_data()

prices = st.session_state["prices"]
returns = st.session_state["returns"]
tickers = st.session_state.get("tickers", [])
ticker_names = st.session_state.get("ticker_names", {})
rf = st.session_state.get("risk_free_rate", 0.04)
init_inv = st.session_state.get("initial_investment", 10000)

equal_w = {t: 1.0 / len(tickers) for t in tickers}
port_ret = build_portfolio_returns(prices, equal_w)
port_ann_ret = annualized_return(port_ret)
port_vol = annualized_volatility(port_ret)
port_sharpe = sharpe_ratio(port_ret, rf=rf)
port_mdd = max_drawdown(port_ret)
port_cagr = cagr(port_ret)
total_return = (1 + port_ret).prod() - 1
gain = init_inv * total_return

kpis = [
    {"label": label("Total Return"), "value": f"${gain:+,.0f}", "delta": f"{total_return:.2%} on ${init_inv:,.0f}", "delta_positive": total_return >= 0},
    {"label": label("CAGR"), "value": f"{port_cagr:.2%}", "delta_positive": port_cagr >= 0},
    {"label": label("Sharpe Ratio"), "value": f"{port_sharpe:.3f}", "delta_positive": port_sharpe >= 1.0},
    {"label": label("Volatility"), "value": f"{port_vol:.2%}", "delta_positive": False},
    {"label": label("Max Drawdown"), "value": f"{port_mdd:.2%}", "delta_positive": False},
]
from src.styles import render_kpi_row
render_kpi_row(kpis)

render_recommendation_banner(prices, returns, tickers, rf)

divider()

tab_labels = ["Performance", "Data Explorer", "Correlation", "Asset Rankings", "Raw Data"]
if is_beginner():
    tab_labels = ["Performance", "Data Explorer", "Correlation", "Asset Rankings", "Raw Data"]
tab_perf, tab_data, tab_corr, tab_rank, tab_raw = st.tabs(tab_labels)

with tab_perf:
    if is_beginner():
        st.caption("All prices start at 100 so you can compare different investments fairly.")
    else:
        st.caption("All prices rebased to 100 so you can compare performance across very different assets.")
    normalized = prices / prices.iloc[0] * 100
    fig = go.Figure()
    colors = chart_colors(len(normalized.columns))
    for i, col in enumerate(normalized.columns):
        lbl = f"{col} \u2014 {ticker_names.get(col, col)}"
        fig.add_trace(go.Scatter(x=normalized.index, y=normalized[col], name=lbl, mode="lines",
                                 line=dict(color=colors[i])))
    fig.update_layout(yaxis_title="Normalized (Base=100)", xaxis_title="Date")
    apply_theme(fig, height=550)
    st.plotly_chart(fig, use_container_width=True)

with tab_data:
    if is_beginner():
        st.caption("Left: daily percentage changes. Right: how those changes are distributed.")
    else:
        st.caption("Left: daily percentage returns over time. Right: return distribution.")
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Returns Over Time", "Distribution"))
    colors = chart_colors(len(returns.columns))
    for i, col in enumerate(returns.columns):
        fig.add_trace(go.Scatter(x=returns.index, y=returns[col], name=col, mode="lines", opacity=0.6,
                                 line=dict(color=colors[i])), row=1, col=1)
    for i, col in enumerate(returns.columns):
        fig.add_trace(go.Histogram(x=returns[col], name=col, opacity=0.5, nbinsx=100,
                                   marker_color=colors[i]), row=1, col=2)
    fig.update_layout(barmode="overlay")
    apply_theme(fig, height=500)
    st.plotly_chart(fig, use_container_width=True)

    section_title("\U0001f4cb Summary Statistics")
    if is_beginner():
        st.caption("count = number of trading days, mean = average daily change, std = daily price swings, min/max = worst/best single day.")
    else:
        st.caption("count = number of trading days, mean = average daily return, std = daily volatility, min/max = worst/best single day.")
    summary = returns.describe()
    st.dataframe(summary.style.format("{:.6f}"), use_container_width=True)
    render_export_section(summary, "returns_summary.csv", key="dashboard_summary")

with tab_corr:
    if is_beginner():
        st.caption("How assets move together. **+1** = always move the same way, **0** = no connection, **-1** = move in opposite directions. Mixing assets with low numbers gives better diversification.")
    else:
        st.caption("How assets move together. **+1** = move in lockstep, **0** = no relationship, **-1** = move in opposite directions. Diversification works best with low/negative correlations.")
    corr = returns.corr()
    fig = make_heatmap(corr.values, corr.columns, corr.index, height=500)
    st.plotly_chart(fig, use_container_width=True)

with tab_rank:
    section_title("\U0001f3c6 Asset Rankings" if not is_beginner() else "\U0001f4cb Investment Scores")
    asset_data = []
    for t in tickers:
        r = returns[t]
        asset_data.append({
            "Ticker": t,
            "Name": ticker_names.get(t, ""),
            label("Return"): annualized_return(r),
            label("Volatility"): annualized_volatility(r),
            label("Sharpe"): sharpe_ratio(r, rf=rf),
            label("Max DD"): max_drawdown(r),
        })
    asset_df = pd.DataFrame(asset_data)

    pct_cols = [c for c in [label("Return"), label("Volatility"), label("Max DD")] if c in asset_df.columns]
    float_cols = [label("Sharpe")]
    fmt_dict = {}
    for c in pct_cols:
        fmt_dict[c] = "{:.2%}"
    for c in float_cols:
        fmt_dict[c] = "{:.3f}"

    styled = asset_df.style.format(fmt_dict)

    def _color_val(val):
        if isinstance(val, float):
            if val > 0:
                return "color: #00d4aa"
            elif val < 0:
                return "color: #e45756"
        return ""

    for c in pct_cols + float_cols:
        if c in asset_df.columns:
            styled = styled.map(_color_val, subset=[c])

    st.dataframe(styled, use_container_width=True, hide_index=True,
                 height=min(400, 50 + len(tickers) * 35))

with tab_raw:
    section_title("Raw Prices")
    st.caption("The actual closing prices downloaded from Yahoo Finance.")
    st.dataframe(prices, use_container_width=True)
    render_export_section(prices, "prices.csv", key="dashboard_prices")

divider()
render_next_button("Risk", "2_Risk.py")
