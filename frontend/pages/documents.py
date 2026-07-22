import streamlit as st

from utils.api_client import (
    APIClientError,
    delete_document,
    get_indexed_documents,
    get_s3_documents,
    reindex_document,
    sync_documents,
    upload_document,
)
from utils.theme import badge, page_header, section_title

page_header(
    "Document Management",
    "Browse, upload, and manage documents in the AWS S3 knowledge repository",
    "📁",
)

EXTENSION_ICONS = {
    "pdf": "📕",
    "docx": "📘",
    "doc": "📘",
    "txt": "📄",
}

if "s3_documents" not in st.session_state:
    st.session_state.s3_documents = []
if "indexed_status" not in st.session_state:
    st.session_state.indexed_status = {}


def refresh_indexed_status() -> None:
    try:
        result = get_indexed_documents()
        st.session_state.indexed_status = {
            doc["s3_key"]: doc for doc in result.get("documents", [])
        }
    except APIClientError:
        pass


upload_tab, browse_tab = st.tabs(["⬆️ Upload", "🗂️ Browse & Manage"])

with upload_tab:
    section_title("Upload a new document", "⬆️")
    uploaded_file = st.file_uploader(
        "Choose a PDF, TXT, or DOCX file",
        type=["pdf", "txt", "docx"],
    )

    folder_choice = st.selectbox(
        "Department folder",
        ["(none — upload to root)", "hr", "it", "finance", "operations", "Other..."],
        help="Matches this bucket's existing Documents/<department>/ layout.",
    )
    if folder_choice == "Other...":
        folder = st.text_input("Custom folder name", placeholder="e.g. legal")
    elif folder_choice == "(none — upload to root)":
        folder = None
    else:
        folder = folder_choice

    if uploaded_file is not None and st.button("Upload & index", type="primary"):
        with st.spinner(f"Uploading and indexing {uploaded_file.name}..."):
            try:
                result = upload_document(uploaded_file.name, uploaded_file.getvalue(), folder=folder)
                st.success(
                    f"Indexed **{result['filename']}** — "
                    f"{result['chunk_count']} chunks, {result['indexed_count']} vectors stored."
                )
                refresh_indexed_status()
            except APIClientError as exc:
                st.error(str(exc))

    st.divider()
    section_title("Sync from S3", "🔄")
    st.caption(
        "Scans the S3 bucket and indexes any new or changed documents. "
        "Unchanged documents (same ETag) are skipped automatically."
    )
    if st.button("🔄 Sync from S3", use_container_width=False):
        with st.spinner("Syncing documents from S3..."):
            try:
                result = sync_documents()
                st.success(
                    f"Indexed {len(result['indexed'])}, "
                    f"skipped {len(result['skipped'])} unchanged, "
                    f"{len(result['failed'])} failed "
                    f"(of {result['total_s3_documents']} total)."
                )
                if result["failed"]:
                    for failure in result["failed"]:
                        st.error(f"{failure['s3_key']}: {failure['error']}")
                refresh_indexed_status()
            except APIClientError as exc:
                st.error(str(exc))

with browse_tab:
    button_col, _ = st.columns([1, 3])
    with button_col:
        load_clicked = st.button(
            "🔄 Load documents from S3",
            type="primary",
            use_container_width=True,
        )

    if load_clicked:
        try:
            result = get_s3_documents()
            st.session_state.s3_documents = result.get("documents", [])
            st.success(f'Found {result.get("count", 0)} supported documents.')
            refresh_indexed_status()
        except APIClientError as exc:
            st.error(str(exc))

    documents = st.session_state.s3_documents

    if not documents:
        st.info(
            "No documents loaded yet. Click **Load documents from S3** "
            "to retrieve the file list."
        )
    else:
        st.write("")
        section_title(f"Available documents ({len(documents)})", "🗂️")

        for document in documents:
            filename = document.get("filename", "Unknown file")
            s3_key = document.get("key", "")
            extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            icon = EXTENSION_ICONS.get(extension, "📄")
            size_kb = document.get("size_bytes", 0) / 1024
            indexed = st.session_state.indexed_status.get(s3_key)

            with st.container(border=True):
                icon_col, name_col, meta_col, action_col = st.columns([0.5, 3, 1.5, 2])

                with icon_col:
                    st.markdown(
                        f"<div style='font-size:1.6rem;'>{icon}</div>",
                        unsafe_allow_html=True,
                    )

                with name_col:
                    st.markdown(f"**{filename}**")
                    st.caption(s3_key)

                with meta_col:
                    st.markdown(f"**{size_kb:.1f} KB**")
                    if indexed and indexed["status"] == "indexed":
                        badge(f"{indexed['chunk_count']} chunks indexed", status="good")
                    elif indexed and indexed["status"] == "failed":
                        badge("Indexing failed", status="critical")
                    else:
                        badge("Not indexed", status="neutral")

                with action_col:
                    reindex_clicked = st.button(
                        "♻️ Reindex", key=f"reindex_{s3_key}", use_container_width=True
                    )
                    delete_clicked = st.button(
                        "🗑️ Delete vectors", key=f"delete_{s3_key}", use_container_width=True
                    )

                if reindex_clicked:
                    with st.spinner(f"Reindexing {filename}..."):
                        try:
                            result = reindex_document(s3_key, filename)
                            st.success(f"Reindexed: {result['indexed_count']} vectors stored.")
                            refresh_indexed_status()
                            st.rerun()
                        except APIClientError as exc:
                            st.error(str(exc))

                if delete_clicked:
                    with st.spinner(f"Deleting vectors for {filename}..."):
                        try:
                            delete_document(s3_key, delete_source=False)
                            st.success("Vectors deleted from Qdrant.")
                            refresh_indexed_status()
                            st.rerun()
                        except APIClientError as exc:
                            st.error(str(exc))
