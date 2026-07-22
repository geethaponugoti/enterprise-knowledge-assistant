from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agent import router as agent_router
from app.api.assistant import router as assistant_router
from app.api.documents import router as documents_router
from app.api.monitoring import router as monitoring_router
from app.config import get_settings
from app.db import init_db
from app.services.qdrant_service import qdrant_health


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Enterprise Knowledge Assistant API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(assistant_router)
app.include_router(agent_router)
app.include_router(monitoring_router)


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "healthy",
        "service": "enterprise-knowledge-assistant",
    }


@app.get("/health/qdrant")
def health_check_qdrant() -> dict:
    return qdrant_health()

@app.get("/debug/settings")
def debug_settings():
    settings = get_settings()

    return {
        "aws_region": settings.aws_region,
        "aws_s3_bucket": settings.aws_s3_bucket,
        "aws_s3_prefix": settings.aws_s3_prefix,
    }