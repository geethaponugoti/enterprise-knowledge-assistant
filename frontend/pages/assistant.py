import streamlit as st

from utils.api_client import APIClientError, ask_assistant
from utils.chat_store import clear_messages, load_messages, save_messages
from utils.theme import badge, page_header

header_col, clear_col = st.columns([5, 1])

with header_col:
    page_header("AI Assistant", "Ask questions about your indexed enterprise documents", "💬")

with clear_col:
    st.write("")
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.chat_messages = []
        clear_messages()
        st.rerun()

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = load_messages()

if not st.session_state.chat_messages:
    st.markdown(
        "Try asking things like:\n"
        "- *What is the remote work policy?*\n"
        "- *How many vacation days do employees get?*\n"
        "- *What's the process for setting up VPN access?*"
    )
    st.divider()


def render_sources(sources: list[dict]) -> None:
    for source in sources:
        relevance_pct = round(source.get("score", 0) * 100)
        with st.expander(
            f"📄 {source.get('filename', 'Unknown')} — page {source.get('page', 1)} "
            f"· {relevance_pct}% relevant"
        ):
            st.progress(min(max(source.get("score", 0), 0.0), 1.0))
            st.markdown(source.get("excerpt", ""))


def render_assistant_message(
    content: str,
    grounded: bool,
    sources: list[dict],
    retrieval_latency_ms: float | None = None,
    generation_latency_ms: float | None = None,
) -> None:
    st.markdown(content)

    if grounded:
        badge("Answered from your documents", status="good")
    else:
        badge("Not found in your documents", status="warning")

    if retrieval_latency_ms is not None and generation_latency_ms is not None:
        st.caption(
            f"⏱️ Retrieval {retrieval_latency_ms:.0f} ms · "
            f"Generation {generation_latency_ms:.0f} ms"
        )

    if sources:
        st.write("")
        st.caption(f"Sources ({len(sources)})")
        render_sources(sources)


for message in st.session_state.chat_messages:
    avatar = "🧑‍💼" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        if message["role"] == "assistant":
            render_assistant_message(
                message["content"],
                message.get("grounded", False),
                message.get("sources", []),
                message.get("retrieval_latency_ms"),
                message.get("generation_latency_ms"),
            )
        else:
            st.markdown(message["content"])

question = st.chat_input("Ask a question about your enterprise documents")

if question:
    st.session_state.chat_messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Searching documents and generating an answer..."):
            try:
                result = ask_assistant(question)
                answer = result.get("answer", "")
                grounded = result.get("grounded", False)
                sources = result.get("sources", [])
                retrieval_latency_ms = result.get("retrieval_latency_ms")
                generation_latency_ms = result.get("generation_latency_ms")

            except APIClientError as exc:
                answer = f"Sorry, I couldn't process that question: {exc}"
                grounded = False
                sources = []
                retrieval_latency_ms = None
                generation_latency_ms = None

        render_assistant_message(
            answer, grounded, sources, retrieval_latency_ms, generation_latency_ms
        )

    st.session_state.chat_messages.append(
        {
            "role": "assistant",
            "content": answer,
            "grounded": grounded,
            "sources": sources,
            "retrieval_latency_ms": retrieval_latency_ms,
            "generation_latency_ms": generation_latency_ms,
        }
    )
    save_messages(st.session_state.chat_messages)
