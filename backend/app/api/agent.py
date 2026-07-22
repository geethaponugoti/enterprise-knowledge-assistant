import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.graph import run_agent

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentRunRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    thread_id: str | None = None


@router.post("/run")
def run_agent_endpoint(request: AgentRunRequest) -> dict:
    thread_id = request.thread_id or str(uuid.uuid4())

    try:
        return run_agent(request.question, thread_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
