from pydantic import BaseModel,Field
from typing import List,Optional

# ---------------------------------------------------------------------------
# Product Embedding
# ---------------------------------------------------------------------------   

class ProductEmbedRequest(BaseModel):
    """
    Input untuk embed 1 produk.
    semua field digabung menjadi 1 string terstruktur → 1 vector embedding.
    """
    
    name: str = Field(
        ...,
        description="Nama produk.",
        examples=["Roti Coklat Lembut"],
    )
    
    category : str = Field(
        ...,
        description="Kategori produk.",
        examples=["Roti Manis"]
    )
    
    description: Optional[str] = Field(
        default=None,
        description="Deskripsi produk. Jika null, hanya name + category yang di-embed.",
        examples=["Roti lembut dengan isian coklat premium, cocok untuk sarapan."]
    )
    
    normalize: bool = Field(
        default=True,
        description="Normalisasi vector ke unit length. Disarankan True untuk cosine similarity."
    )
    
class ProductEmbedResponse(BaseModel):
    """1 produk -> 1 vector embedding."""
    embedding: list[float] = Field(
        ...,
        description="Vector embedding produk."
    )
    text_input : str = Field(
        ...,
        description="String gabungan yang dikirim ke model (untuk debugging/audit)."
    )
    dimension: int = Field(
        ...,
        description="Dimensi vector embedding."
    )
    
    model : str = Field(
        ...,
        description="Nama model yang digunakan."
    )
    
    
# ---------------------------------------------------------------------------
# Similarity
# ---------------------------------------------------------------------------

class SimilarityRequest(BaseModel):
    """
    Hitung cosine similarity antara 2 produk.
    berguna untuk cek seberapa mirip 2 produk sebelum menyimpan ke DB.
    """
    
    product_a: ProductEmbedRequest
    product_b: ProductEmbedRequest
    
class SimilarityResponse(BaseModel):
    score: float = Field(
        ...,
        description="Cosine similarity score antara -1 dan 1. Semakin dekat ke 1, semakin mirip."
    )
    interpretation: str = Field(
        ...,
        description="Interpretasi human-readable dari score."
    )