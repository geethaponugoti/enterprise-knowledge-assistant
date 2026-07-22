import streamlit as st

from utils.theme import inject_css, sidebar_brand

st.set_page_config(
    page_title="Enterprise Knowledge Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

with st.sidebar:
    sidebar_brand()

pages = {
    "Knowledge Platform": [
        st.Page(
            "pages/home.py",
            title="Home",
            icon="🏠",
            default=True,
        ),
        st.Page(
            "pages/dashboard.py",
            title="Dashboard",
            icon="📊",
        ),
        st.Page(
            "pages/documents.py",
            title="Documents",
            icon="📁",
        ),
        st.Page(
            "pages/assistant.py",
            title="AI Assistant",
            icon="💬",
        ),
        st.Page(
            "pages/agent_monitor.py",
            title="Agent Monitor",
            icon="🤖",
        ),
    ]
}

navigation = st.navigation(pages)
navigation.run()