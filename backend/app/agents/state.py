import operator
from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    trace: Annotated[list[dict], operator.add]
    step_count: Annotated[int, operator.add]
