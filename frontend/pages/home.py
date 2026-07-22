import streamlit as st

from utils.theme import card, hero, section_title

hero(
    "Enterprise Knowledge Assistant",
    "An agentic RAG platform that turns your S3 document library into "
    "instant, source-backed answers.",
)

section_title("How it works", "🧭")

workflow_cols = st.columns(4)
workflow_steps = [
    ("📥", "Ingest", "Documents are pulled from AWS S3 and split into chunks."),
    ("🧠", "Embed", "OpenAI embeddings turn each chunk into a searchable vector."),
    ("🔎", "Retrieve", "Qdrant finds the most relevant chunks for a question."),
    ("🤖", "Answer", "An AI agent drafts an answer with cited sources."),
]
for column, (icon, title, body) in zip(workflow_cols, workflow_steps):
    with column:
        card(title, body, icon)

st.write("")
section_title("What you can do here", "✨")

feature_cols = st.columns(3)
features = [
    ("📊", "Dashboard", "Monitor the health of the backend, vector store and document pipeline."),
    ("📁", "Documents", "Browse the enterprise documents available in the knowledge base."),
    ("💬", "AI Assistant", "Ask natural-language questions and get grounded, cited answers."),
]
for column, (icon, title, body) in zip(feature_cols, features):
    with column:
        card(title, body, icon)

st.write("")
st.info(
    "🚧 Current milestone: frontend, FastAPI, AWS S3 and Qdrant connections "
    "are verified. RAG question answering and agent tools are next."
)
