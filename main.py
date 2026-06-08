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
from services.embedding.routes.embed import router as embed_router
from services.embedding.routes.recommend import router as recommend_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    async with AsyncSessionLocal() as db:
        await db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await db.commit()

        result = await db.execute(text("SELECT version()"))
        pg_version = result.scalar()
        print(f"✅ Connected to database. PostgreSQL version: {pg_version}")

    print("🚀 Loading embedding model...")
    app.state.embedding_model = EmbeddingModel()
    print("✅ Embedding model loaded.")

    yield

    # SHUTDOWN
    print("🛑 Shutting down...")
    await engine.dispose()
    print("✅ Database connections closed.")


app = FastAPI(
    title="Klangenan AI Services",
    description="Microservice AI: Embedding, dan layanan AI lainnya.",
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware dulu, baru router
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(embed_router, prefix=settings.API_PREFIX, tags=["Embedding"])
app.include_router(recommend_router, prefix=settings.API_PREFIX, tags=["Recommendation"])


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Klangenan AI is running 🎯"}