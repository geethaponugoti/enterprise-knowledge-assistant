import uuid

import streamlit as st

from utils.api_client import APIClientError, get_monitoring_stats, run_agent
from utils.theme import badge, page_header, section_title, step

page_header(
    "Agent Monitor",
    "Ask multi-step questions and inspect the agent's execution trace",
    "🤖",
)

if "agent_thread_id" not in st.session_state:
    st.session_state.agent_thread_id = str(uuid.uuid4())
if "agent_history" not in st.session_state:
    st.session_state.agent_history = []

STATUS_STYLE = {
    "success": "good",
    "step_limit_reached": "warning",
    "error": "critical",
}

with st.expander("💡 Try a multi-step question"):
    st.markdown(
        "- *Compare the employee handbook with the leave policy.*\n"
        "- *How many finance documents are in S3, and summarize the travel policy?*\n"
        "- *List IT documents and answer how employees reset their VPN password.*"
    )

question = st.chat_input("Ask the agent a multi-step question")

if question:
    with st.spinner("Agent is working — this may call multiple tools..."):
        try:
            result = run_agent(question, st.session_state.agent_thread_id)
        except APIClientError as exc:
            result = {"error": str(exc)}

    st.session_state.agent_history.append({"question": question, "result": result})

section_title("Conversation", "💬")

if not st.session_state.agent_history:
    st.info("Ask a question above to see the agent's plan, tool calls, and execution trace.")

for entry in reversed(st.session_state.agent_history):
    with st.container(border=True):
        st.markdown(f"**Question:** {entry['question']}")

        result = entry["result"]
        if "error" in result:
            st.error(result["error"])
            continue

        st.markdown(result["answer"])

        status = result.get("status", "success")
        badge(status.replace("_", " ").title(), status=STATUS_STYLE.get(status, "neutral"))

        if result.get("tools_used"):
            st.caption("Tools used: " + ", ".join(result["tools_used"]))

        st.caption(
            f"{result.get('step_count', 0)} steps · "
            f"{result.get('latency_ms', 0):.0f} ms total"
        )

        trace = result.get("trace", [])
        with st.expander(f"Execution trace ({len(trace)} steps)"):
            for index, trace_entry in enumerate(trace, start=1):
                if trace_entry["step"] == "agent":
                    label = "🧠 Agent reasoning"
                    if trace_entry.get("tool_calls"):
                        label += f" → calling {', '.join(trace_entry['tool_calls'])}"
                    else:
                        label += " → final answer"
                else:
                    label = f"🔧 Tool: {trace_entry['tool']}"

                step(index, f"{label} ({trace_entry['latency_ms']:.0f} ms)")

                if trace_entry["step"] == "tool":
                    st.caption(f"Input: {trace_entry['input']}")
                    st.caption(f"Output: {trace_entry['output_summary']}")
                    if trace_entry.get("error"):
                        st.error(trace_entry["error"])

st.divider()
section_title("Recent agent executions (all sessions)", "🧵")

try:
    stats = get_monitoring_stats()
    recent_runs = stats.get("recent_agent_runs", [])

    if not recent_runs:
        st.caption("No agent runs recorded yet.")
    else:
        for run in recent_runs:
            with st.container(border=True):
                info_col, status_col = st.columns([4, 1])
                with info_col:
                    st.markdown(f"**{run['question']}**")
                    st.caption(f"Tools: {', '.join(run['tools_used']) or 'none'}")
                with status_col:
                    badge(
                        run["status"].replace("_", " ").title(),
                        status=STATUS_STYLE.get(run["status"], "neutral"),
                    )
                    st.caption(f"{run['latency_ms']:.0f} ms")
except APIClientError as exc:
    st.error(str(exc))
