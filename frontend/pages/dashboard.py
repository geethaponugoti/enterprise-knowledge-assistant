import streamlit as st

from utils.api_client import (
    APIClientError,
    get_health,
    get_monitoring_stats,
    get_qdrant_health,
    get_s3_documents,
)
from utils.theme import page_header, section_title, stat_tile

page_header("Dashboard", "Live system health and knowledge-base overview", "📊")

fastapi_connected = False
qdrant_connected = False
document_count = 0
collection_count = 0

try:
    get_health()
    fastapi_connected = True
except APIClientError:
    pass

try:
    qdrant_data = get_qdrant_health()
    qdrant_connected = True
    collection_count = len(qdrant_data.get("collections", []))
except APIClientError:
    pass

try:
    document_data = get_s3_documents()
    document_count = document_data.get("count", 0)
except APIClientError:
    pass

column1, column2, column3, column4 = st.columns(4)

with column1:
    stat_tile(
        "FastAPI Backend",
        "Connected" if fastapi_connected else "Unavailable",
        status="good" if fastapi_connected else "critical",
    )

with column2:
    stat_tile(
        "Qdrant Vector DB",
        "Connected" if qdrant_connected else "Unavailable",
        status="good" if qdrant_connected else "critical",
    )

with column3:
    stat_tile("S3 Documents", str(document_count), status="neutral", icon="📄")

with column4:
    stat_tile("Qdrant Collections", str(collection_count), status="neutral", icon="🗂️")

st.write("")
st.write("")

try:
    stats = get_monitoring_stats()

    section_title("Knowledge base", "📚")
    kb_col1, kb_col2, kb_col3 = st.columns(3)
    with kb_col1:
        stat_tile("Indexed Documents", str(stats["indexed_document_count"]), icon="✅")
    with kb_col2:
        qdrant_points = stats["qdrant_point_count"]
        stat_tile(
            "Qdrant Vectors",
            str(qdrant_points) if qdrant_points is not None else "Unavailable",
            status="neutral" if qdrant_points is not None else "critical",
            icon="🧬",
        )
    with kb_col3:
        s3_count = stats["s3_document_count"]
        stat_tile(
            "S3 Documents",
            str(s3_count) if s3_count is not None else "Unavailable",
            status="neutral" if s3_count is not None else "critical",
            icon="📄",
        )

    st.write("")
    section_title("Usage and performance", "⚡")
    usage_col1, usage_col2, usage_col3, usage_col4 = st.columns(4)
    with usage_col1:
        stat_tile("Questions Asked", str(stats["questions_asked"]), icon="💬")
    with usage_col2:
        stat_tile("Agent Runs", str(stats["agent_runs"]), icon="🤖")
    with usage_col3:
        stat_tile(
            "Avg Retrieval Latency",
            f"{stats['avg_retrieval_latency_ms']:.0f} ms",
            icon="🔎",
        )
    with usage_col4:
        stat_tile(
            "Avg Generation Latency",
            f"{stats['avg_generation_latency_ms']:.0f} ms",
            icon="✍️",
        )

    st.write("")
    section_title("Recent errors", "⚠️")
    recent_errors = stats.get("recent_errors", [])
    if not recent_errors:
        st.caption("No recent errors recorded.")
    else:
        for error in recent_errors:
            with st.container(border=True):
                st.markdown(f"**{error['question']}**")
                st.caption(error["created_at"])
                st.error(error["error"])

except APIClientError as exc:
    st.warning(f"Monitoring stats unavailable: {exc}")
