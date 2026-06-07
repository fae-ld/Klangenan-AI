"""
Route: /embed/bread
 
Dipanggil oleh Next.js setiap kali:
- Admin menambahkan roti baru (CREATE)
- Admin mengupdate nama / kategori / deskripsi roti (UPDATE)
 
Tidak perlu dipanggil saat update harga, stok, gambar, atau URL marketplace.
"""
 
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
 
from ..database.connection import get_db
from ..repositories.bread_repository import BreadRepository
 
router = APIRouter(prefix="/embed", tags=["Embedding"])
 
 
# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
 
class BreadEmbedRequest(BaseModel):
    bread_id: int
    name: str
    category: str
    description: str = ""
    normalize: bool = True
 
 
class BreadEmbedResponse(BaseModel):
    bread_id: int
    saved: bool
    text_input: str   # string yang di-embed, untuk debugging
    dimension: int
    model: str
 
 
# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
 
@router.post(
    "/bread",
    response_model=BreadEmbedResponse,
    summary="Embed satu roti → simpan vector ke DB",
)
async def embed_bread(
    request: Request,
    body: BreadEmbedRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate embedding untuk satu roti dan langsung simpan ke database.
 
    **Kapan dipanggil:**
    - `CREATE` — roti baru ditambahkan admin
    - `UPDATE` — nama / kategori / deskripsi berubah
 
    **Tidak perlu dipanggil saat:** update harga, stok, gambar, atau URL marketplace
    karena field tersebut tidak mempengaruhi makna semantik.
    """
    model = request.app.state.embedding_model
    repo = BreadRepository(db)
 
    # 1. Build text input dari field semantik
    text_input = model.build_product_text(
        name=body.name,
        category=body.category,
        description=body.description,
    )
 
    # 2. Generate embedding
    try:
        embedding = model.encode_single(text_input, normalize=body.normalize)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal membuat embedding: {e}")
 
    # 3. Simpan ke DB
    saved = await repo.save_embedding(
        bread_id=body.bread_id,
        embedding=embedding,
    )
 
    if not saved:
        raise HTTPException(
            status_code=404,
            detail=f"Roti dengan ID {body.bread_id} tidak ditemukan di database",
        )
 
    return BreadEmbedResponse(
        bread_id=body.bread_id,
        saved=saved,
        text_input=text_input,
        dimension=model.dimension,
        model=model.MODEL_NAME,
    )
 
 
@router.post(
    "/bread/batch",
    summary="Bulk embed — semua roti yang belum punya embedding",
)
async def embed_batch(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Re-embed semua roti yang belum punya embedding.
 
    Berguna saat:
    - Pertama kali setup (data roti sudah ada tapi belum di-embed)
    - Ganti model sentence-transformers ke versi baru
    """
    model = request.app.state.embedding_model
    repo = BreadRepository(db)
 
    breads = await repo.get_all_without_embedding()
 
    if not breads:
        return {"message": "Semua roti sudah punya embedding", "processed": 0}
 
    success_count = 0
    failed_ids = []
 
    for bread in breads:
        try:
            text_input = model.build_product_text(
                name=bread.name,
                category=bread.category,
                description=bread.description or "",
            )
            embedding = model.encode_single(text_input, normalize=True)
            await repo.save_embedding(bread.id, embedding)
            success_count += 1
        except Exception as e:
            failed_ids.append({"id": bread.id, "error": str(e)})
 
    return {
        "message": f"Berhasil embed {success_count} dari {len(breads)} roti",
        "processed": success_count,
        "failed": failed_ids,
    }