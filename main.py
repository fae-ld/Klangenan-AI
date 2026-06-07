import os
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Load .env jika ada (opsional, tidak error kalau file tidak ada)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Set HF_TOKEN agar Hugging Face tidak throttle download model
if not os.getenv("HF_TOKEN"):
    print("⚠️  HF_TOKEN tidak di-set. Download model mungkin lebih lambat.")

from services.embedding.router import router as embedding_router
from services.embedding.model import EmbeddingModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Loading embedding model...")
    app.state.embedding_model = EmbeddingModel()
    print("✅ Embedding model loaded.")
    yield
    print("🛑 Shutting down...")


app = FastAPI(
    title="Klangenan AI Services",
    description="Microservice AI: Embedding, dan layanan AI lainnya.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(embedding_router, prefix="/api/v1/embedding", tags=["Embedding"])


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Klangenan AI is running 🎯"}
