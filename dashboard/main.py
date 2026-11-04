"""Streamlit frontend for the uploaded FastAPI agent."""
import os

import requests
import streamlit as st

API_URL = os.getenv("API_BASE_URL", "http://api:8000").rstrip("/")

st.set_page_config(
    page_title="Agentic AI | Workflow Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {padding-top: 1.8rem; max-width: 1250px;}
.hero {border:1px solid rgba(125,132,245,.24); border-radius:20px;
  padding:1.5rem 1.8rem; margin-bottom:1rem;
  background:linear-gradient(115deg,rgba(88,92,231,.17),rgba(33,174,180,.06));}
.hero h1 {font-size:2.1rem; margin:0 0 .35rem 0; letter-spacing:-.03em;}
.hero p {margin:.2rem 0; color:#9eaac5;}
.stChatMessage {border-radius:16px;}
.subtle {color:#8b98ad; font-size:.84rem;}
</style>
""", unsafe_allow_html=True)


def get_json(path: str):
    response = requests.get(f"{API_URL}{path}", timeout=6)
    response.raise_for_status()
    return response.json()


def get_status():
    try:
        return get_json("/health"), None
    except requests.RequestException as exc:
        return None, str(exc)


if "messages" not in st.session_state:
    st.session_state.messages = []

status, connection_error = get_status()
with st.sidebar:
    st.markdown("### 🤖 Agentic AI")
    st.caption("Workflow Assistant • Local developer edition")
    st.divider()
    if connection_error:
        st.error("Backend offline")
        st.caption(connection_error)
    else:
        st.success("Backend online")
        if status.get("model_configured"):
            st.caption("OpenAI API key detected in backend")
        else:
            st.warning("OpenAI API key is missing")
    st.markdown("**Environment**")
    st.code(API_URL, language=None)
    st.caption("Tools: local task list + live UTC clock")
    st.caption("MCP server is separate; no agent-to-MCP connection yet.")
    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.markdown("**Example questions**")
    examples = [
        "What are my open project tasks?",
        "Which demo tasks are completed?",
        "What time is it in UTC?",
        "Can you mark task 1 as done?",
    ]
    for i, example in enumerate(examples):
        if st.button(example, key=f"sample_{i}", use_container_width=True):
            st.session_state.pending_prompt = example
    st.divider()
    st.caption("🔒 Local demo only. Do not expose these ports to the public Internet without authentication.")

st.markdown("""
<div class="hero">
  <h1>✦ Agentic AI Workflow Assistant</h1>
  <p>LangChain / LangGraph-powered reasoning · FastAPI backend · Docker Compose</p>
  <p class="subtle">Ask about sample tasks or current UTC time, and inspect actual agent responses.</p>
</div>
""", unsafe_allow_html=True)

chat_tab, tasks_tab, system_tab = st.tabs(["💬 Agent Chat", "📋 Demo Tasks", "🛠️ System Status"])

with chat_tab:
    if not st.session_state.messages:
        st.info("Welcome! Try asking **What are my open project tasks?** to call the agent's real local task tool.")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    incoming = st.chat_input("Ask the agent about tasks or time…", max_chars=2000, disabled=bool(connection_error))
    prompt = st.session_state.pop("pending_prompt", None) or incoming
    if prompt and not connection_error:
        prior = st.session_state.messages[-12:]
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Agent is thinking and calling tools…"):
                try:
                    response = requests.post(
                        f"{API_URL}/ask",
                        json={"question": prompt, "history": prior},
                        timeout=120,
                    )
                    if not response.ok:
                        try:
                            detail = response.json().get("detail", response.text)
                        except ValueError:
                            detail = response.text
                        st.error(f"API error {response.status_code}: {detail}")
                    else:
                        answer = response.json()["answer"]
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                except requests.RequestException as exc:
                    st.error(f"Cannot reach agent API: {exc}")
    st.caption("Conversation is stored only in this Streamlit browser session. Recent turns are sent to FastAPI for context.")

with tasks_tab:
    st.subheader("Sample project tasks")
    st.warning("These tasks are fictional, hard-coded data. They cannot be edited or persisted yet.")
    try:
        task_payload = get_json("/tasks")
        tasks = task_payload["tasks"]
        a, b, c = st.columns(3)
        a.metric("Total tasks", len(tasks))
        b.metric("Open", sum(t["status"] == "open" for t in tasks))
        c.metric("Completed", sum(t["status"] == "done" for t in tasks))
        st.dataframe(tasks, hide_index=True, use_container_width=True)
        if st.button("↻ Refresh tasks"):
            st.rerun()
    except (requests.RequestException, KeyError, ValueError) as exc:
        st.error(f"Could not retrieve tasks: {exc}")

with system_tab:
    st.subheader("Runtime checks")
    if connection_error:
        st.error("FastAPI is unreachable from the dashboard container")
    else:
        st.success("GET /health returned 200 OK")
        st.json(status)
    st.markdown("**API endpoints**")
    st.code("GET /health\nGET /tasks\nPOST /ask", language="text")
    st.markdown("**Architecture note**")
    st.info("The FastAPI agent uses Python-local tools. mcp_server.py is supplied as a separate MCP prototype and is not used by this dashboard.")
    st.markdown("**Debugging**")
    st.code("docker compose ps\ndocker compose logs -f api dashboard", language="bash")
