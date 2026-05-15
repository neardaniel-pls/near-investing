import streamlit as st


def render_export_section(data, filename: str, label: str = "Download CSV", key: str = None):
    csv = data.to_csv()
    btn_key = f"dl_{key or filename}"
    st.download_button(
        f"{label}",
        csv,
        file_name=filename,
        mime="text/csv",
        key=btn_key,
    )


def render_export_row(exports: list):
    cols = st.columns(len(exports))
    for col, exp in zip(cols, exports):
        with col:
            csv = exp["data"].to_csv()
            st.download_button(
                exp.get("label", "Download CSV"),
                csv,
                file_name=exp["filename"],
                mime="text/csv",
                key=exp.get("key", f"dl_{exp['filename']}"),
            )


def render_portfolio_summary_md(weights: dict, metrics: dict, date_range: tuple = None, initial_investment: float = None) -> str:
    lines = ["# Portfolio Summary\n"]
    if date_range:
        lines.append(f"**Period:** {date_range[0]} to {date_range[1]}\n")
    if initial_investment:
        lines.append(f"**Initial Investment:** ${initial_investment:,.0f}\n")
    lines.append("## Allocation\n")
    for t, w in sorted(weights.items(), key=lambda x: -x[1]):
        if abs(w) > 0.001:
            lines.append(f"- **{t}**: {w:.2%}")
    lines.append("\n## Key Metrics\n")
    for k, v in metrics.items():
        if isinstance(v, float):
            if abs(v) < 1:
                lines.append(f"- **{k}**: {v:.3f}")
            else:
                lines.append(f"- **{k}**: {v:,.2f}")
        else:
            lines.append(f"- **{k}**: {v}")
    return "\n".join(lines)
