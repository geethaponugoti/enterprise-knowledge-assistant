import time

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import tools_condition

from app.agents.state import AgentState
from app.agents.tools import ALL_TOOLS
from app.config import get_settings
from app.db import DB_PATH
from app.repositories.agent_run_repository import log_agent_run

AGENT_SYSTEM_PROMPT = (
    "You are an enterprise knowledge assistant agent with access to tools "
    "for searching, summarizing, comparing, and inspecting indexed company "
    "documents. Break multi-part questions into the necessary tool calls, "
    "one step at a time. Only answer from tool results — never fabricate "
    "information about documents you have not retrieved. When you have "
    "enough information, respond with a final answer that cites the "
    "documents you used."
)

CHECKPOINT_DB_PATH = str(DB_PATH.parent / "agent_checkpoints.db")
TOOLS_BY_NAME = {tool.name: tool for tool in ALL_TOOLS}


def _agent_node(state: AgentState) -> dict:
    settings = get_settings()
    model = ChatOpenAI(model=settings.chat_model, api_key=settings.openai_api_key)
    model_with_tools = model.bind_tools(ALL_TOOLS)

    messages = [SystemMessage(content=AGENT_SYSTEM_PROMPT), *state["messages"]]

    started = time.perf_counter()
    response = model_with_tools.invoke(messages)
    latency_ms = (time.perf_counter() - started) * 1000

    trace_entry = {
        "step": "agent",
        "latency_ms": round(latency_ms, 1),
        "tool_calls": [call["name"] for call in (response.tool_calls or [])],
    }

    return {"messages": [response], "trace": [trace_entry], "step_count": 1}


def _tools_node(state: AgentState) -> dict:
    last_message = state["messages"][-1]
    tool_messages = []
    trace_entries = []

    for call in last_message.tool_calls:
        tool_fn = TOOLS_BY_NAME.get(call["name"])
        started = time.perf_counter()

        try:
            result = tool_fn.invoke(call["args"]) if tool_fn else f"Unknown tool: {call['name']}"
            error = None
        except Exception as exc:  # external boundary: tool bodies call OpenAI, Qdrant, S3 and the DB with heterogeneous exception types
            result = f"Tool error: {exc}"
            error = str(exc)

        latency_ms = (time.perf_counter() - started) * 1000
        summary = str(result)
        if len(summary) > 500:
            summary = summary[:500] + "..."

        tool_messages.append(
            ToolMessage(content=str(result), tool_call_id=call["id"], name=call["name"])
        )
        trace_entries.append(
            {
                "step": "tool",
                "tool": call["name"],
                "input": call["args"],
                "output_summary": summary,
                "latency_ms": round(latency_ms, 1),
                "error": error,
            }
        )

    return {"messages": tool_messages, "trace": trace_entries, "step_count": 1}


def _route(state: AgentState) -> str:
    settings = get_settings()
    if state.get("step_count", 0) >= settings.agent_max_steps:
        return END
    return tools_condition(state)


def _build_graph() -> StateGraph:
    builder = StateGraph(AgentState)
    builder.add_node("agent", _agent_node)
    builder.add_node("tools", _tools_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", _route, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")

    return builder


def run_agent(question: str, thread_id: str) -> dict:
    settings = get_settings()
    builder = _build_graph()

    started = time.perf_counter()
    status = "success"

    try:
        with SqliteSaver.from_conn_string(CHECKPOINT_DB_PATH) as checkpointer:
            graph = builder.compile(checkpointer=checkpointer)
            config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": settings.agent_max_steps * 2 + 4,
            }
            final_state = graph.invoke(
                {
                    "messages": [HumanMessage(content=question)],
                    "trace": [],
                    "step_count": 0,
                },
                config=config,
            )
    except Exception as exc:  # external boundary: the LangGraph engine plus every tool/LLM call beneath it
        latency_ms = (time.perf_counter() - started) * 1000
        log_agent_run(thread_id, question, "error", [], [], 0, latency_ms, error=str(exc))
        raise RuntimeError(f"Agent run failed: {exc}") from exc

    latency_ms = (time.perf_counter() - started) * 1000

    final_answer = ""
    for message in reversed(final_state["messages"]):
        if message.type == "ai" and not getattr(message, "tool_calls", None):
            final_answer = message.content
            break

    trace = final_state.get("trace", [])
    tools_used = sorted({entry["tool"] for entry in trace if entry.get("step") == "tool"})
    step_count = final_state.get("step_count", 0)

    if step_count >= settings.agent_max_steps:
        status = "step_limit_reached"

    log_agent_run(thread_id, question, status, tools_used, trace, step_count, latency_ms)

    return {
        "answer": final_answer,
        "thread_id": thread_id,
        "status": status,
        "tools_used": tools_used,
        "trace": trace,
        "step_count": step_count,
        "latency_ms": round(latency_ms, 1),
    }
