"""
Entry point FastAPI — Klangenan AI Microservice
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pgvector.sqlalchemy import Vector  # noqa: F401
from sqlalchemy import text

from services.embedding.config import settings
from services.embedding.database.connection import AsyncSessionLocal, engine
from services.embedding.model import EmbeddingModel
from services.embedding.llm.factory import get_llm
from services.embedding.routes.embed import router as embed_router
from services.embedding.routes.recommend import router as recommend_router
from services.embedding.routes.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    async with AsyncSessionLocal() as db:
        await db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await db.commit()
        result = await db.execute(text("SELECT version()"))
        pg_version = result.scalar()
        print(f"✅ Database connected: {pg_version[:50]}...")

    print("🚀 Loading embedding model...")
    app.state.embedding_model = EmbeddingModel()
    print(f"✅ Embedding model loaded: {app.state.embedding_model.MODEL_NAME}")

    print(f"🤖 Loading LLM provider: {settings.LLM_PROVIDER}...")
    app.state.llm = get_llm()
    print(f"✅ LLM loaded: {settings.LLM_PROVIDER}")

    yield

    # SHUTDOWN
    print("🛑 Shutting down...")
    await engine.dispose()
    print("✅ Shutdown complete")


app = FastAPI(
    title="Klangenan AI Services",
    description="Microservice AI: Embedding, Rekomendasi, dan Chatbot.",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(embed_router, prefix=settings.API_PREFIX, tags=["Embedding"])
app.include_router(recommend_router, prefix=settings.API_PREFIX, tags=["Recommendation"])
app.include_router(chat_router, prefix=settings.API_PREFIX, tags=["Chatbot"])


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "message": "Klangenan AI is running 🎯",
        "llm_provider": settings.LLM_PROVIDER,
    }