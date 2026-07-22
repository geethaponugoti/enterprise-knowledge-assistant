from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.rag_service import answer_question

router = APIRouter(prefix="/assistant", tags=["assistant"])


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    score_threshold: float | None = Field(default=None, ge=0.0, le=1.0)


@router.post("/ask")
def ask_question(request: AskRequest) -> dict:
    try:
        return answer_question(
            request.question,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
