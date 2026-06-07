"""
ProductRepository — semua query DB untuk tabel products.
 
Pola repository memisahkan logic DB dari route handler,
sehingga mudah di-mock saat unit testing.
 
Operasi yang dihandle FastAPI:
  - Simpan embedding produk baru
  - Update embedding saat produk diubah
  - Query similarity search (rekomendasi)
  - Cek apakah produk sudah punya embedding
"""

from sqalchemy import select,update
from sqalchemy.ext.asyncio import AsyncSession

from ..models.bread import Bread, EMBEDDING_DIM

class BreadRepository:
    def __init__(self,db: AsyncSession):
        self.db = db
        
    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------
    
    async def get_by_id(self,bread_id: int) -> Bread | None:
        """ambil 1 produk berdasarkan ID."""
        result = await self.db.execute(
            select(Bread).where(Bread.id == bread_id)
        )
        return result.scalar_one_or_none()
    
    
    async def get_embedding(self,bread_id: int)-> list[float] | None:
        """Ambil hanya kolom embedding (lebih ringan dari full SELECT)."""
        result = await self.db.execute(
            select(Bread.embedding).where(Bread.id == bread_id)
        )
        row = result.fetchone()
        return row.embedding if row else None
    
    async def get_all_without_embedding(self) -> list[Bread]:
        """
        Ambil semua produk yang belum punya embedding.
        Berguna untuk bulk re-embed saat model diganti.
        """
        result = await self.db.execute(
            select(Bread)
            .where(Bread.embedding.is_(None))
            .where(Bread.is_active == True)
        )
        return list(result.scalars().all())
    
    
    # ------------------------------------------------------------------
    # WRITE
    # ------------------------------------------------------------------
    
    async def save_embedding(self,bread_id:int, embedding: list[float]) -> None:
        """
        Simpan atau update embedding untuk produk tertentu.
        Return True jika berhasil, False jika produk tidak ditemukan.
        """
        if len(embedding) != EMBEDDING_DIM:
            raise ValueError(
                f"Dimensi embedding tidak sesuai: expected {EMBEDDING_DIM}, "
                f"got {len(embedding)}"
            )
            
        result = await self.db.execute(
            update(Bread)
            .where(Bread.id == bread_id)
            .values(embedding=embedding)
            .returning(Bread.id)
        )
        updated = result.fetchone()
        return updated is not None
    
    # ------------------------------------------------------------------
    # SIMILARITY SEARCH
    # ------------------------------------------------------------------
 
    async def find_similar(
        self,
        source_embedding: list[float],
        exclude_ids: list[int],
        top_k: int = 5,
        category_filter: str | None = None,
        min_similarity: float = 0.5,
    ) -> list[dict]:
        """
        Cari produk paling mirip menggunakan cosine distance (<=>).
 
        pgvector cosine distance: 0 = identik, 2 = berlawanan
        Similarity score = 1 - cosine_distance  (range 0.0 – 1.0)
 
        Args:
            source_embedding : vector produk yang sedang dilihat user
            exclude_ids      : list ID yang dikecualikan (minimal [source_product_id])
            top_k            : jumlah hasil yang dikembalikan
            category_filter  : opsional, filter kategori yang sama
            min_similarity   : threshold minimum similarity (default 0.5)
 
        Returns:
            list of dict: [{id, name, category, price, image_url, similarity_score}]
        """
        # Cosine similarity = 1 - cosine distance
        cosine_distance = Bread.embedding.op("<=>")(source_embedding)
        similarity_score = (1 - cosine_distance).label("similarity_score")
 
        query = (
            select(
                Bread.id,
                Bread.name,
                Bread.category,
                Bread.price,
                Bread.image_url,
                similarity_score,
            )
            .where(Bread.is_active == True)
            .where(Bread.embedding.is_not(None))           # skip produk tanpa embedding
            .where(Bread.id.notin_(exclude_ids))           # exclude source + blacklist
            .where((1 - cosine_distance) >= min_similarity)  # threshold
            .order_by(cosine_distance)                       # ascending = paling mirip dulu
            .limit(top_k)
        )
 
        # Filter kategori opsional
        if category_filter:
            query = query.where(Bread.category == category_filter)
 
        result = await self.db.execute(query)
        rows = result.fetchall()
 
        return [
            {
                "id": row.id,
                "name": row.name,
                "category": row.category,
                "price": float(row.price),
                "image_url": row.image_url,
                "similarity_score": round(float(row.similarity_score), 4),
            }
            for row in rows
        ]