import plotly.graph_objects as go
import numpy as np
from src.styles import CHART_PALETTE


def chart_colors(n: int) -> list:
    return [CHART_PALETTE[i % len(CHART_PALETTE)] for i in range(n)]


def apply_theme(fig: go.Figure, height: int = 500) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=50, r=30, t=30, b=50),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#fafafa", size=12),
        legend=dict(
            orientation="h",
            y=1.02,
            font=dict(size=11),
        ),
        hovermode="x unified",
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.03)",
            zerolinecolor="rgba(255,255,255,0.08)",
            rangeslider=dict(visible=False),
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(label="ALL", step="all"),
                ],
                font=dict(size=10, color="#888"),
                bgcolor="#1e2235",
                activecolor="rgba(0,212,170,0.2)",
                bordercolor="rgba(255,255,255,0.08)",
            ) if height >= 400 else dict(),
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.03)",
            zerolinecolor="rgba(255,255,255,0.08)",
        ),
        dragmode="zoom",
    )
    return fig


def make_line_chart(data_dict: dict, y_title: str = "", height: int = 500) -> go.Figure:
    fig = go.Figure()
    colors = chart_colors(len(data_dict))
    for i, (name, series) in enumerate(data_dict.items()):
        fig.add_trace(go.Scatter(
            x=series.index,
            y=series.values,
            name=name,
            mode="lines",
            line=dict(color=colors[i], width=1.5),
        ))
    fig.update_layout(yaxis_title=y_title, xaxis_title="Date")
    apply_theme(fig, height=height)
    return fig


def make_pie_chart(labels: list, values: list, height: int = 350) -> go.Figure:
    colors = chart_colors(len(labels))
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.45,
        marker=dict(colors=colors, line=dict(color="#1a1d29", width=2)),
        textinfo="label+percent",
        textfont=dict(size=11),
        hovertemplate="<b>%{label}</b><br>%{value:.1f}%<extra></extra>",
    ))
    apply_theme(fig, height=height)
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", y=-0.05, font=dict(size=10)),
        margin=dict(l=20, r=20, t=30, b=30),
    )
    return fig


def make_bar_chart(categories: list, values_dict: dict, y_title: str = "", barmode: str = "group", height: int = 500) -> go.Figure:
    fig = go.Figure()
    colors = chart_colors(len(values_dict))
    for i, (name, values) in enumerate(values_dict.items()):
        fig.add_trace(go.Bar(
            x=categories,
            y=values,
            name=name,
            marker_color=colors[i],
        ))
    fig.update_layout(barmode=barmode, yaxis_title=y_title)
    apply_theme(fig, height=height)
    return fig


def make_heatmap(z, x, y, colorscale: str = "RdBu", zmin=-1, zmax=1, height: int = 500) -> go.Figure:
    fig = go.Figure(go.Heatmap(
        z=z, x=x, y=y,
        colorscale=colorscale, zmin=zmin, zmax=zmax,
        text=[[f"{v:.3f}" if isinstance(v, float) else str(v) for v in row] for row in z],
        texttemplate="%{text}",
        textfont=dict(size=10),
    ))
    apply_theme(fig, height=height)
    return fig


def make_scatter_plot(points: list, x_title: str = "", y_title: str = "", height: int = 450) -> go.Figure:
    fig = go.Figure()
    colors = chart_colors(len(points))
    for i, pt in enumerate(points):
        fig.add_trace(go.Scatter(
            x=[pt["x"]],
            y=[pt["y"]],
            mode="markers+text",
            name=pt.get("name", ""),
            text=[pt.get("name", "")],
            textposition="top center",
            marker=dict(
                size=pt.get("size", 12),
                color=pt.get("color", colors[i]),
                symbol=pt.get("symbol", "circle"),
            ),
        ))
    fig.update_layout(xaxis_title=x_title, yaxis_title=y_title)
    apply_theme(fig, height=height)
    return fig


def format_dataframe_styler(df, highlight_max_cols=None, pct_cols=None, float_precision=4):
    styler = df.style

    pct_set = {c for c in (pct_cols or []) if c in df.columns}
    if pct_set:
        styler = styler.format({c: "{:.2%}" for c in pct_set}, na_rep="\u2014")

    def _fmt_num(v):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if isinstance(v, float) and np.isnan(v):
                return "\u2014"
            return f"{v:.{float_precision}f}"
        return v

    def _color_positive_negative(val):
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            if isinstance(val, float) and np.isnan(val):
                return ""
            if val > 0:
                return "color: #00d4aa"
            elif val < 0:
                return "color: #e45756"
        return ""

    numeric_cols = [c for c in df.columns if np.issubdtype(df[c].dtype, np.number)]
    non_pct_numeric = [c for c in numeric_cols if c not in pct_set]
    if non_pct_numeric:
        styler = styler.format({c: _fmt_num for c in non_pct_numeric})

    for col in numeric_cols:
        styler = styler.map(_color_positive_negative, subset=[col])

    if highlight_max_cols:
        for col in highlight_max_cols:
            if col in df.columns:
                try:
                    styler = styler.highlight_max(subset=[col], color="#00d4aa22", axis=0)
                except Exception:
                    pass

    return styler
