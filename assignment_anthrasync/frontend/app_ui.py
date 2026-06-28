import json
from typing import Any

import httpx
import streamlit as st

st.set_page_config(
    page_title="Aethera Sync Interactive UI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

STYLE = """
<style>
body {
    background: radial-gradient(circle at top left, #1a3f66, #0d1724);
    color: #f5f7fb;
}
section.main > div {
    background: rgba(255, 255, 255, 0.03);
    border-radius: 24px;
    padding: 20px;
}
.stButton > button {
    border-radius: 999px;
    background: linear-gradient(135deg, #6c9df9 0%, #a463ff 100%);
    color: white;
    font-weight: 600;
}
.stTextInput > div > input,
.stTextArea > div > textarea {
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.08);
    color: #f5f7fb;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.metrics-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 16px;
}
.metric-card {
    padding: 18px;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.08);
}
.metric-card h4 {
    margin: 0 0 8px 0;
    font-weight: 700;
}
.metric-card p {
    margin: 0;
    font-size: 1rem;
    color: #d8e0f2;
}
.chat-bubble {
    border-radius: 22px;
    padding: 18px;
    margin: 8px 0;
    max-width: 90%;
}
.chat-user {
    background: rgba(106, 196, 255, 0.16);
    border: 1px solid rgba(106, 196, 255, 0.25);
}
.chat-assistant {
    background: rgba(166, 99, 255, 0.16);
    border: 1px solid rgba(166, 99, 255, 0.25);
}
.chat-stream {
    max-height: 520px;
    overflow-y: auto;
}
</style>
"""

PAGE_HEADER = "Aethera Sync — Intelligent RAG Assistant"
PAGE_SUBHEADER = (
    "An interactive Streamlit workspace for your deployed Hybrid RAG backend, "
    "with chat history, source insights, and query intelligence."  # noqa: E501
)

DEFAULT_API_URL = "https://eshwar109-assignment-anthra.hf.space"


def inject_style() -> None:
    st.markdown(STYLE, unsafe_allow_html=True)


def ensure_state() -> None:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "api_url" not in st.session_state:
        st.session_state.api_url = DEFAULT_API_URL
    if "health_status" not in st.session_state:
        st.session_state.health_status = "Not checked"


def normalize_endpoint(url: str, endpoint: str) -> str:
    url = url.strip()
    if url.endswith(endpoint):
        return url
    return f"{url.rstrip('/')}{endpoint}"


def call_api(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(normalize_endpoint(url, "/ask"), json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"API error {exc.response.status_code}: {exc.response.text}") from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"Unable to connect to backend: {exc}") from exc


def check_health(url: str) -> str:
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(normalize_endpoint(url, "/health"))
            response.raise_for_status()
            metadata = response.json()
            return metadata.get("message", "Backend reachable")
    except Exception as exc:
        return f"Health check failed: {exc}"


def render_metric_card(title: str, value: str) -> None:
    st.markdown(
        f"""
        <div class='metric-card'>
            <h4>{title}</h4>
            <p>{value}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat_history() -> None:
    if not st.session_state.chat_history:
        st.info("Ask a question to start the conversation and see your RAG assistant in action.")
        return

    for item in st.session_state.chat_history:
        role = item["role"]
        content = item["content"]
        card = "chat-user" if role == "user" else "chat-assistant"
        st.markdown(
            f"<div class='chat-bubble {card}'><strong>{role.title()}:</strong><br>{content}</div>",
            unsafe_allow_html=True,
        )


def render_response_details(response: dict[str, Any]) -> None:
    with st.expander("🔍 Answer details", expanded=True):
        st.markdown("### Final answer")
        st.write(response["answer"])

        tabs = st.tabs(["Query insights", "Sources", "Raw response"])
        with tabs[0]:
            st.write("**Original question**")
            st.write(response.get("query", "-"))
            st.write("**Optimized retrieval query**")
            st.write(response.get("optimized_query", "-"))

            metric_items = response.get("metrics", {}) or {}
            st.markdown("<div class='metrics-container'>", unsafe_allow_html=True)
            render_metric_card("Retrieval count", str(metric_items.get("retrieval_count", "N/A")))
            render_metric_card("Query tokens", str(metric_items.get("query_tokens", "N/A")))
            render_metric_card("Elapsed ms", str(metric_items.get("elapsed_ms", "N/A")))
            render_metric_card("Faithfulness", f"{metric_items.get('faithfulness', 'N/A')}")
            render_metric_card("Relevance", f"{metric_items.get('relevance', 'N/A')}")
            render_metric_card("Context recall", f"{metric_items.get('context_recall', 'N/A')}")
            st.markdown("</div>", unsafe_allow_html=True)

        with tabs[1]:
            documents = response.get("context_documents", [])
            if documents:
                for idx, doc in enumerate(documents, 1):
                    st.write(f"**{idx}.** {doc}")
            else:
                st.write("No context documents were returned.")

        with tabs[2]:
            st.code(json.dumps(response, indent=2, ensure_ascii=False), language="json")


def main() -> None:
    inject_style()
    ensure_state()

    with st.sidebar:
        st.markdown("## Backend settings")
        st.session_state.api_url = st.text_input(
            "API base URL",
            value=st.session_state.api_url,
            help="Enter your deployed FastAPI backend URL, e.g. https://example.com",
        )
        if st.button("Check backend"):  # noqa: SIM102
            st.session_state.health_status = check_health(st.session_state.api_url)
        st.markdown(f"**Health:** {st.session_state.health_status}")
        st.markdown("---")
        st.markdown("## Tips")
        st.write(
            "- Use a clear enterprise query.\n"
            "- The assistant shows sources and retrieval metrics.\n"
            "- Save your backend URL so you can refresh quickly."
        )
        st.markdown("---")
        st.markdown("## Quick walk-through")
        st.write(
            "1. Enter the deployed backend URL.\n"
            "2. Ask a question.\n"
            "3. Review answer, sources, and query diagnostics."
        )

    st.markdown(f"# {PAGE_HEADER}")
    st.markdown(f"*{PAGE_SUBHEADER}*")

    left, right = st.columns([2, 1])
    with left:
        st.markdown("### Ask your knowledge base")
        question = st.text_area("Your question", height=140, key="question_input")
        submit = st.button("Send question", type="primary")
        if submit and question.strip():
            payload = {"question": question.strip()}
            with st.spinner("Sending your question to the backend..."):
                try:
                    result = call_api(st.session_state.api_url, payload)
                    st.session_state.chat_history.append({"role": "user", "content": question.strip()})
                    st.session_state.chat_history.append({"role": "assistant", "content": result.get("answer", "No answer returned.")})
                    st.session_state.last_response = result
                except RuntimeError as exc:
                    st.error(str(exc))
                    st.session_state.last_response = None
                    result = None

        if st.session_state.chat_history:
            st.markdown("### Conversation")
            st.markdown("<div class='chat-stream'>", unsafe_allow_html=True)
            render_chat_history()
            st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("### Session summary")
        st.metric("Questions asked", len([x for x in st.session_state.chat_history if x["role"] == "user"]))
        st.metric("Responses received", len([x for x in st.session_state.chat_history if x["role"] == "assistant"]))

        if st.session_state.get("last_response"):
            st.markdown("### Latest response")
            render_response_details(st.session_state.last_response)

    if st.session_state.get("last_response") and not submit:
        pass


if __name__ == "__main__":
    main()
