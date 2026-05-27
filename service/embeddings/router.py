from fastapi import APIRouter, Request,HTTPException
from .schemas import (
    ProductEmbedRequest,
    ProductEmbedResponse,
    SimilarityRequest,
    SimilarityResponse,
)

router = APIRouter()

@router.post(
    "/product",
    response_model=ProductEmbedResponse,
    summary="Embed 1 produk → 1 vector",
)
def embed_product(request: Request, body: ProductEmbedRequest):
    """
    Mengubah data produk (name, category, description) menjadi **1 vector embedding**.

    Flow:
    1. Field produk digabung: `"nama: X | kategori: Y | deskripsi: Z"`
    2. String gabungan di-encode → 1 vector float
    3. Simpan vector ini ke database (pgvector) untuk similarity search

    Gunakan endpoint ini saat:
    - Produk baru dibuat (`CREATE`)
    - Data produk diupdate (`UPDATE`) → embed ulang dan update vector di DB
    """
    model = request.app.state.embedding_model
    
    text_input = model.build_product_text(
        name=body.name,
        category=body.category,
        description=body.description,
    )
    
    try:
        embedding = model.encode_single(text_input, normalize=body.normalize)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal membuat embedding: {str(e)}")
    
    return ProductEmbedResponse(
        embedding=embedding,
        text_input=text_input,
        dimension=model.dimension,
        model=model.MODEL_NAME,
    )
    
@router.post(
    "/similarity",
    response_model=SimilarityResponse,
    summary="Hitung kemiripan antara 2 produk",
)
def compute_similarity(request: Request, body: SimilarityRequest):
    """
    Hitung **cosine similarity** antara 2 produk secara langsung.

    Score antara -1 dan 1:
    - `>= 0.90` → Sangat mirip
    - `>= 0.75` → Mirip
    - `>= 0.50` → Cukup mirip
    - `< 0.25`  → Tidak mirip

    Cocok untuk testing/debugging. Untuk rekomendasi produk di production,
    gunakan pgvector di database langsung (lebih efisien untuk N produk).
    """
    
    model = request.app.state.embedding_model
    
    try :
        text_a = model.build_product_text(
            name=body.product_a.name,
            category=body.product_a.category,
            description=body.product_a.description,
        )
        text_b = model.build_product_text(
            name=body.product_b.name,
            category=body.product_b.category,
            description=body.product_b.description,
        )
        
        vec_a = model.encode_single(text_a, normalize=True)
        vec_b = model.encode_single(text_b, normalize=True)
        
        score = model.cosine_similarity(vec_a, vec_b)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menghitung similarity: {str(e)}")
    
    return SimilarityResponse(
        score=round(score,4),
        interpretation=model.interpret_similarity(score),
    )
    
@router.get("/info", summary="Info model embedding yang aktif")
def get_model_info(request: Request):
    """Menampilkan informasi model embedding yang sedang aktif."""
    model = request.app.state.embedding_model
    return {
        "model": model.MODEL_NAME,
        "dimension": model.dimension,
    }
        