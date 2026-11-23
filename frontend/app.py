"""Streamlit interface for DocuMind."""

import re

import streamlit as st

import api_client as api

st.set_page_config(page_title="DocuMind", page_icon="📄", layout="centered")

STATUS_BADGES = {
    "pending": ("Queued", "gray"),
    "processing": ("Processing", "blue"),
    "ready": ("Ready", "green"),
    "failed": ("Failed", "red"),
}

NOT_FOUND = "I could not find this in the uploaded documents."
CITATION = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")


def is_not_found(answer: str) -> bool:
    return answer.strip() == NOT_FOUND


def cite_files(text: str, sources: list) -> str:
    """Replace [n] with the file name and page of source n."""

    def replace(match: re.Match) -> str:
        labels = []
        for number in re.findall(r"\d+", match.group(1)):
            index = int(number)
            if not 1 <= index <= len(sources):
                return match.group(0)
            source = sources[index - 1]
            labels.append(f"{source['filename']}, page {source['page']}")
        return "(" + "; ".join(labels) + ")"

    return CITATION.sub(replace, text)

st.session_state.setdefault("messages", [])
st.session_state.setdefault("upload_picker", 0)


def documents_page() -> None:
    st.title("Documents")

    notice = st.session_state.pop("document_notice", None)
    if notice:
        st.success(notice)

    with st.container(border=True):
        st.subheader("Upload a document")
        file = st.file_uploader(
            "Choose a PDF or TXT file",
            type=["pdf", "txt"],
            key=f"upload_{st.session_state.upload_picker}",
        )
        upload = st.button("Upload", type="primary", disabled=file is None)

    heading, actions = st.columns([3, 2], vertical_alignment="center")
    heading.subheader("Document library")
    actions.button("Refresh status", help="Check whether uploaded documents are ready.")

    try:
        documents = api.list_documents()
    except api.ApiError as exc:
        st.error(exc.detail)
        return

    if upload and file is not None:
        try:
            api.upload_document(
                file.name, file.getvalue(), file.type or "application/octet-stream"
            )
        except api.ApiError as exc:
            st.error(exc.detail)
            if exc.status == 0:
                return
        else:
            st.session_state.document_notice = "Upload accepted. Check its status below."
            st.session_state.upload_picker += 1
            st.rerun()

    if not documents:
        st.info("No documents yet. Upload a PDF or TXT file to get started.")
        return

    for document in documents:
        with st.container(border=True):
            name, status, action = st.columns([4, 2, 2], vertical_alignment="center")
            name.text(document["filename"])
            label, color = STATUS_BADGES.get(document["status"], ("Unknown", "gray"))
            status.badge(label, color=color)

            if action.button("Delete", key=f"delete_{document['id']}"):
                try:
                    api.delete_document(document["id"])
                except api.ApiError as exc:
                    st.error(exc.detail)
                else:
                    st.session_state.document_notice = "Document deleted."
                    st.rerun()

            if document["status"] == "failed" and document.get("error_message"):
                st.text(document["error_message"])


def show_message(role: str, content: str, sources: list | None = None) -> None:
    with st.chat_message(role):
        if role == "user":
            st.text(content)
        else:
            st.markdown(cite_files(content, sources or []))

        if sources and not is_not_found(content):
            with st.expander(f"Sources ({len(sources)})"):
                for index, source in enumerate(sources, start=1):
                    st.text(f"[{index}] {source['filename']} · Page {source['page']}")
                    st.text(source["snippet"])


def chat_page() -> None:
    title, actions = st.columns([4, 2], vertical_alignment="center")
    title.title("Ask your documents")

    messages = st.session_state.messages
    if actions.button("Clear chat", disabled=not messages):
        messages.clear()
        st.session_state.pop("chat_error", None)

    if not messages:
        st.info("Upload a document, wait until it is Ready, then ask a question about it.")

    for message in messages:
        show_message(**message)

    question = st.chat_input("Ask a question about your documents", max_chars=2000)
    if question and question.strip():
        st.session_state.pop("chat_error", None)
        user_message = {"role": "user", "content": question.strip()}
        messages.append(user_message)
        show_message(**user_message)

        try:
            with st.spinner("Searching your documents…"):
                result = api.ask(user_message["content"])
        except api.ApiError as exc:
            st.session_state.chat_error = exc.detail
        else:
            reply = {
                "role": "assistant",
                "content": result["answer"],
                "sources": result["sources"],
            }
            messages.append(reply)
            show_message(**reply)

    if st.session_state.get("chat_error"):
        st.error(st.session_state.chat_error)


st.sidebar.title("📄 DocuMind")
page = st.sidebar.radio("Page", ["Chat", "Documents"], label_visibility="collapsed")

if page == "Chat":
    chat_page()
else:
    documents_page()
