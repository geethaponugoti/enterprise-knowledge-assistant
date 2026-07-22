"""Shared visual design system for the Streamlit frontend."""

import streamlit as st

PRIMARY = "#2a78d6"
PRIMARY_DARK = "#184f95"
SURFACE = "#ffffff"
BORDER = "rgba(11,11,11,0.08)"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#898781"

STATUS = {
    "good": {"color": "#0ca30c", "bg": "#e6f7e6", "icon": "✅"},
    "warning": {"color": "#b97400", "bg": "#fff4e0", "icon": "⚠️"},
    "serious": {"color": "#c1502a", "bg": "#fdeae1", "icon": "🔶"},
    "critical": {"color": "#d03b3b", "bg": "#fbe4e4", "icon": "⛔"},
    "neutral": {"color": "#52514e", "bg": "#f1f1ef", "icon": "•"},
}


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{
            font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
        }}
        .block-container {{
            padding-top: 2.25rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }}

        .ek-brand {{
            display: flex; align-items: center; gap: 0.65rem;
            padding: 0.5rem 0.25rem 1.1rem 0.25rem;
            border-bottom: 1px solid {BORDER};
            margin-bottom: 0.85rem;
        }}
        .ek-brand-icon {{
            font-size: 1.4rem; width: 40px; height: 40px; flex-shrink: 0;
            display: flex; align-items: center; justify-content: center;
            background: linear-gradient(135deg, {PRIMARY}, {PRIMARY_DARK});
            border-radius: 10px; color: white;
        }}
        .ek-brand-title {{ font-weight: 700; font-size: 1rem; line-height: 1.15; color: {TEXT_PRIMARY}; }}
        .ek-brand-sub {{ font-size: 0.74rem; color: {TEXT_MUTED}; }}

        .ek-hero {{
            background: linear-gradient(135deg, {PRIMARY} 0%, #1c5cab 55%, {PRIMARY_DARK} 100%);
            border-radius: 16px;
            padding: 2.2rem 2.5rem;
            color: white;
            margin-bottom: 1.75rem;
            box-shadow: 0 8px 24px rgba(24,79,149,0.22);
        }}
        .ek-hero h1 {{ margin: 0 0 0.45rem 0; font-size: 1.95rem; color: white; }}
        .ek-hero p {{ margin: 0; opacity: 0.94; font-size: 1.03rem; max-width: 660px; }}

        .ek-card {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 1.2rem 1.35rem;
            box-shadow: 0 1px 2px rgba(11,11,11,0.04);
            height: 100%;
        }}
        .ek-card h4 {{ margin: 0 0 0.35rem 0; font-size: 0.98rem; color: {TEXT_PRIMARY}; }}
        .ek-card p {{ margin: 0; color: {TEXT_SECONDARY}; font-size: 0.87rem; line-height: 1.45; }}

        .ek-page-title {{
            font-size: 1.65rem; font-weight: 700; color: {TEXT_PRIMARY};
            margin: 0; display: flex; align-items: center; gap: 0.5rem;
        }}
        .ek-section-title {{
            font-size: 1.08rem; font-weight: 700; color: {TEXT_PRIMARY};
            margin: 0.2rem 0 0.85rem 0;
            display: flex; align-items: center; gap: 0.5rem;
        }}

        .ek-stat-tile {{
            background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px;
            padding: 1.05rem 1.2rem; box-shadow: 0 1px 2px rgba(11,11,11,0.04);
        }}
        .ek-stat-label {{
            font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.045em;
            color: {TEXT_MUTED}; font-weight: 700;
        }}
        .ek-stat-value {{ font-size: 1.55rem; font-weight: 700; color: {TEXT_PRIMARY}; margin-top: 0.2rem; }}

        .ek-badge {{
            display: inline-flex; align-items: center; gap: 0.35rem;
            padding: 0.3rem 0.7rem; border-radius: 999px;
            font-size: 0.82rem; font-weight: 600; border: 1px solid transparent;
            width: fit-content; margin-bottom: 0.4rem;
        }}

        .ek-step {{ display: flex; gap: 0.75rem; padding: 0.5rem 0; align-items: flex-start; }}
        .ek-step-index {{
            flex-shrink: 0; width: 26px; height: 26px; border-radius: 50%;
            background: {PRIMARY}; color: white; font-size: 0.78rem; font-weight: 700;
            display: flex; align-items: center; justify-content: center;
        }}
        .ek-step-text {{ padding-top: 0.15rem; color: {TEXT_PRIMARY}; font-size: 0.92rem; }}

        footer {{ visibility: hidden; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def sidebar_brand() -> None:
    st.markdown(
        """
        <div class="ek-brand">
            <div class="ek-brand-icon">📚</div>
            <div>
                <div class="ek-brand-title">Knowledge Assistant</div>
                <div class="ek-brand-sub">Enterprise RAG Platform</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, icon: str = "📚") -> None:
    st.markdown(
        f"""
        <div class="ek-hero">
            <h1>{icon} {title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str | None = None, icon: str = "") -> None:
    st.markdown(
        f'<div class="ek-page-title">{icon} {title}</div>',
        unsafe_allow_html=True,
    )
    if subtitle:
        st.caption(subtitle)
    st.write("")


def section_title(title: str, icon: str = "") -> None:
    st.markdown(
        f'<div class="ek-section-title">{icon} {title}</div>',
        unsafe_allow_html=True,
    )


def stat_tile(label: str, value: str, status: str = "neutral", icon: str | None = None) -> None:
    style = STATUS[status]
    display_icon = icon if icon is not None else style["icon"]
    st.markdown(
        f"""
        <div class="ek-stat-tile">
            <div class="ek-stat-label">{label}</div>
            <div class="ek-stat-value">{display_icon} {value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def badge(text: str, status: str = "neutral") -> None:
    style = STATUS[status]
    st.markdown(
        f'<div class="ek-badge" style="background:{style["bg"]}; '
        f'color:{style["color"]}; border-color:{style["color"]}33;">'
        f'{style["icon"]} {text}</div>',
        unsafe_allow_html=True,
    )


def badge_list(items: list[str], status: str = "neutral") -> None:
    style = STATUS[status]
    rows = "".join(
        f'<div class="ek-badge" style="background:{style["bg"]}; '
        f'color:{style["color"]}; border-color:{style["color"]}33;">'
        f'{style["icon"]} {item}</div>'
        for item in items
    )
    st.markdown(rows, unsafe_allow_html=True)


def card(title: str, body: str, icon: str = "") -> None:
    st.markdown(
        f"""
        <div class="ek-card">
            <h4>{icon} {title}</h4>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def step(index: int, text: str) -> None:
    st.markdown(
        f"""
        <div class="ek-step">
            <div class="ek-step-index">{index}</div>
            <div class="ek-step-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
