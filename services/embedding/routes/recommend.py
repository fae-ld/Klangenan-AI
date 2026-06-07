"""
Route: /recommend

Rekomendasi roti berbasis cosine similarity embedding.
Dipanggil Next.js saat user membuka halaman detail roti.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import get_db
from ..repositories.bread_repository import BreadRepository

router = APIRouter(prefix="/recommend", tags=["Recommendation"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RecommendRequest(BaseModel):
    bread_id: int
    top_k: int = 5
    exclude_ids: list[int] = []
    category_filter: str | None = None
    min_similarity: float = 0.5


class RecommendedBread(BaseModel):
    id: int
    name: str
    category: str
    price: float | None
    image_url: str | None
    gojek_url: str | None
    grab_url: str | None
    shopee_food_url: str | None
    similarity_score: float


class RecommendResponse(BaseModel):
    source_bread_id: int
    recommendations: list[RecommendedBread]
    total: int


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=RecommendResponse,
    summary="Rekomendasi roti berdasarkan cosine similarity",
)
async def recommend_breads(
    body: RecommendRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Cari top-K roti paling mirip dengan roti yang sedang dilihat user.

    Response sudah include URL marketplace (Gojek, Grab, ShopeeFood)
    sehingga Next.js bisa langsung render tombol beli.
    """
    repo = BreadRepository(db)

    # 1. Ambil embedding roti sumber
    source_embedding = await repo.get_embedding(body.bread_id)

    if source_embedding is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Roti ID {body.bread_id} tidak ditemukan atau belum punya embedding. "
                "Pastikan sudah di-embed via POST /api/v1/embed/bread"
            ),
        )

    # 2. Similarity search
    exclude = list(set(body.exclude_ids + [body.bread_id]))

    similar = await repo.find_similar(
        source_embedding=source_embedding,
        exclude_ids=exclude,
        top_k=body.top_k,
        category_filter=body.category_filter,
        min_similarity=body.min_similarity,
    )

    recommendations = [RecommendedBread(**item) for item in similar]

    return RecommendResponse(
        source_bread_id=body.bread_id,
        recommendations=recommendations,
        total=len(recommendations),
    )