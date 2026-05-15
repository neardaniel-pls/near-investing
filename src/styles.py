import streamlit as st


COLORS = {
    "primary": "#00d4aa",
    "primary_dim": "#00d4aa55",
    "primary_bg": "#00d4aa11",
    "bg": "#0e1117",
    "bg_secondary": "#1a1d29",
    "bg_card": "#1e2235",
    "bg_card_hover": "#252a40",
    "text": "#fafafa",
    "text_dim": "#888888",
    "text_muted": "#555555",
    "positive": "#00d4aa",
    "negative": "#e45756",
    "warning": "#f58518",
    "info": "#4c78a8",
    "border": "#ffffff15",
    "border_hover": "#00d4aa44",
    "shadow": "rgba(0,0,0,0.3)",
}

CHART_PALETTE = [
    "#00d4aa", "#4c78a8", "#f58518", "#e45756", "#72b7b2",
    "#54a24b", "#eeca3b", "#b279a2", "#ff9da6", "#9d755d",
    "#9d9d9d", "#d67195", "#8cd17d", "#b6992d", "#499894",
]


def inject_global_styles():
    st.markdown(f"""<style>
    :root {{
        --primary: {COLORS['primary']};
        --primary-dim: {COLORS['primary_dim']};
        --primary-bg: {COLORS['primary_bg']};
        --bg: {COLORS['bg']};
        --bg-secondary: {COLORS['bg_secondary']};
        --bg-card: {COLORS['bg_card']};
        --bg-card-hover: {COLORS['bg_card_hover']};
        --text: {COLORS['text']};
        --text-dim: {COLORS['text_dim']};
        --positive: {COLORS['positive']};
        --negative: {COLORS['negative']};
        --warning: {COLORS['warning']};
        --border: {COLORS['border']};
        --shadow: {COLORS['shadow']};
        --radius: 12px;
        --radius-sm: 8px;
    }}

    .stApp {{
        background-color: var(--bg);
    }}

    .stSidebar {{
        background-color: var(--bg-secondary) !important;
        border-right: 1px solid var(--border);
    }}

    .block-container {{
        padding-top: 3.5rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }}

    header[data-testid="stHeader"] {{
        z-index: 999;
    }}

    h1, h2, h3 {{
        color: var(--text) !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }}

    h1 {{ font-size: 1.8rem !important; margin-bottom: 0.5rem !important; }}
    h2 {{ font-size: 1.4rem !important; margin-bottom: 0.4rem !important; }}
    h3 {{ font-size: 1.15rem !important; margin-bottom: 0.3rem !important; }}

    .stMetric {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1rem 1.2rem !important;
        transition: all 0.2s ease;
    }}
    .stMetric:hover {{
        border-color: var(--border-hover, var(--primary-dim));
        box-shadow: 0 4px 20px var(--shadow);
    }}
    .stMetric > label {{
        font-size: 0.85rem !important;
        color: var(--text-dim) !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .stMetric > div[data-testid="stMetricValue"] {{
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }}

    .card {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.25rem 1.5rem;
        transition: all 0.25s ease;
    }}
    .card:hover {{
        border-color: var(--border-hover, var(--primary-dim));
        box-shadow: 0 4px 20px var(--shadow);
        background: var(--bg-card-hover);
    }}

    .card-flat {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1rem 1.25rem;
    }}

    .badge {{
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    .badge-primary {{
        background: var(--primary-bg);
        color: var(--primary);
        border: 1px solid var(--primary-dim);
    }}
    .badge-positive {{
        background: #00d4aa15;
        color: var(--positive);
        border: 1px solid #00d4aa33;
    }}
    .badge-negative {{
        background: #e4575615;
        color: var(--negative);
        border: 1px solid #e4575633;
    }}
    .badge-warning {{
        background: #f5851815;
        color: var(--warning);
        border: 1px solid #f5851833;
    }}
    .badge-info {{
        background: #4c78a815;
        color: var(--info);
        border: 1px solid #4c78a833;
    }}

    .feature-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }}
    .feature-card {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.25rem;
        cursor: default;
        transition: all 0.25s ease;
        text-align: center;
    }}
    .feature-card:hover {{
        border-color: var(--primary);
        box-shadow: 0 0 25px {COLORS['primary_dim']};
        transform: translateY(-2px);
    }}
    .feature-card .feature-icon {{
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }}
    .feature-card .feature-title {{
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text);
        margin-bottom: 0.3rem;
    }}
    .feature-card .feature-desc {{
        font-size: 0.8rem;
        color: var(--text-dim);
        line-height: 1.4;
    }}

    .step-card {{
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.5rem;
        text-align: center;
        position: relative;
    }}
    .step-card .step-number {{
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: var(--primary-bg);
        border: 2px solid var(--primary);
        color: var(--primary);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 0.75rem;
    }}
    .step-card .step-title {{
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 0.3rem;
    }}
    .step-card .step-desc {{
        font-size: 0.8rem;
        color: var(--text-dim);
    }}

    .page-header {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }}
    .page-header .page-icon {{
        font-size: 1.8rem;
    }}
    .page-header .page-title {{
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--text);
    }}
    .page-header .page-subtitle {{
        font-size: 0.9rem;
        color: var(--text-dim);
    }}

    .nav-bar {{
        display: flex;
        gap: 0.4rem;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
        padding: 0.5rem;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
    }}
    .nav-item {{
        padding: 0.45rem 0.8rem;
        border-radius: var(--radius-sm);
        font-size: 0.78rem;
        font-weight: 500;
        cursor: default;
        transition: all 0.2s ease;
        border: 1px solid var(--border);
        background: var(--bg-card);
        color: var(--text-dim);
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        white-space: nowrap;
        line-height: 1.2;
    }}
    .nav-item:hover {{
        border-color: var(--primary-dim);
        color: var(--text);
    }}
    .nav-item.active {{
        background: var(--primary-bg);
        border-color: var(--primary);
        color: var(--primary);
        font-weight: 600;
    }}

    .divider {{
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--border), transparent);
        margin: 1.5rem 0;
    }}

    .dataframe {{
        border-radius: var(--radius) !important;
        overflow: hidden;
    }}

    .stButton > button {{
        border-radius: var(--radius-sm) !important;
        transition: all 0.2s ease;
    }}
    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 12px var(--shadow);
    }}

    .stSelectbox > div > div {{
        border-radius: var(--radius-sm) !important;
    }}

    .stSlider > div > div > div > div {{
        background: var(--primary) !important;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: var(--radius-sm) var(--radius-sm) 0 0;
        padding: 0.6rem 1.2rem;
    }}

    .stExpander {{
        border-radius: var(--radius) !important;
        border: 1px solid var(--border) !important;
    }}

    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: var(--bg);
    }}
    ::-webkit-scrollbar-thumb {{
        background: var(--border);
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--text-dim);
    }}

    .section-title {{
        font-size: 1.15rem;
        font-weight: 600;
        color: var(--text);
        margin: 1.5rem 0 0.75rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    .mode-toggle {{
        display: flex;
        background: var(--bg-card);
        border-radius: var(--radius-sm);
        padding: 0.2rem;
        border: 1px solid var(--border);
    }}
    .mode-toggle button {{
        flex: 1;
        border: none;
        background: transparent;
        color: var(--text-dim);
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
    }}
    .mode-toggle button.active {{
        background: var(--primary-bg);
        color: var(--primary);
        border: 1px solid var(--primary-dim);
    }}

    .skeleton {{
        background: linear-gradient(90deg, var(--bg-card) 25%, var(--bg-card-hover) 50%, var(--bg-card) 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
        border-radius: var(--radius-sm);
    }}
    @keyframes shimmer {{
        0% {{ background-position: -200% 0; }}
        100% {{ background-position: 200% 0; }}
    }}

    @media (max-width: 768px) {{
        .block-container {{
            padding: 1rem !important;
        }}
        .kpi-grid {{
            grid-template-columns: repeat(2, 1fr);
        }}
        .feature-grid {{
            grid-template-columns: 1fr;
        }}
        h1 {{ font-size: 1.4rem !important; }}
        .stMetric > div[data-testid="stMetricValue"] {{
            font-size: 1.2rem !important;
        }}
        .nav-bar {{
            flex-direction: column;
        }}
        .nav-item {{
            text-align: center;
            justify-content: center;
        }}
    }}

    @media (max-width: 480px) {{
        .kpi-grid {{
            grid-template-columns: 1fr;
        }}
    }}
    </style>""", unsafe_allow_html=True)


def badge(text: str, variant: str = "primary") -> str:
    return f'<span class="badge badge-{variant}">{text}</span>'


def divider():
    st.markdown('<hr class="divider">', unsafe_allow_html=True)


def section_title(title: str, icon: str = ""):
    icon_html = f'<span>{icon}</span>' if icon else ""
    st.markdown(f'<div class="section-title">{icon_html} {title}</div>', unsafe_allow_html=True)


def card(content: str):
    st.markdown(f'<div class="card">{content}</div>', unsafe_allow_html=True)


def card_flat(content: str):
    st.markdown(f'<div class="card-flat">{content}</div>', unsafe_allow_html=True)


def render_kpi_row(kpis: list):
    cols = st.columns(len(kpis))
    for col, kpi in zip(cols, kpis):
        with col:
            st.metric(
                label=kpi["label"],
                value=kpi["value"],
                delta=kpi.get("delta", ""),
                delta_color="normal" if kpi.get("delta_positive", True) else "inverse",
            )


def skeleton_placeholder(lines: int = 3):
    html = '<div style="margin: 1rem 0;">'
    for i in range(lines):
        width = "100%" if i % 2 == 0 else "70%"
        html += f'<div class="skeleton" style="height: 20px; width: {width}; margin-bottom: 0.5rem;"></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
