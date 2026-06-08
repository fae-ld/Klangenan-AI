from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np
from sqlalchemy import text

from ..models.bread import Bread, EMBEDDING_DIM


class BreadRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, bread_id: int) -> Bread | None:
        result = await self.db.execute(
            select(Bread).where(Bread.id == bread_id)
        )
        return result.scalar_one_or_none()

    async def get_embedding(self, bread_id: int) -> list[float] | None:
        result = await self.db.execute(
            select(Bread.embedding).where(Bread.id == bread_id)
        )
        row = result.fetchone()
        if row is None or row.embedding is None:
            return None

        return np.array(row.embedding).flatten().tolist()

    async def get_all_without_embedding(self) -> list[Bread]:
        result = await self.db.execute(
            select(Bread)
            .where(Bread.embedding.is_(None))
            .where(Bread.is_available == True)
        )
        return list(result.scalars().all())

    async def save_embedding(self, bread_id: int, embedding: list[float]) -> bool:
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




    async def find_similar(
        self,
        source_embedding: list[float],
        exclude_ids: list[int],
        top_k: int = 5,
        category_filter: str | None = None,
        min_similarity: float = 0.5,
    ) -> list[dict]:
        # Convert ke plain list of float
        source_embedding = [float(x) for x in np.array(source_embedding).flatten()]
        
        # Embed vector langsung sebagai literal SQL string — hindari masalah parameter casting
        vector_literal = f"'[{','.join(str(x) for x in source_embedding)}]'::vector"
        print(f"Vector literal for SQL: {vector_literal}")  # Debug: pastikan format benar
        
        exclude_ids = list(set(exclude_ids)) if exclude_ids else [-1]
        exclude_str = ",".join(str(i) for i in exclude_ids)

        category_clause = "AND category = :category" if category_filter else ""

        sql = text(f"""
            SELECT 
                id,
                name,
                category,
                price,
                "imageUrl"       AS image_url,
                "gojekUrl"       AS gojek_url,
                "grabUrl"        AS grab_url,
                "shopeeFoodUrl"  AS shopee_food_url,
                1 - (embedding <=> {vector_literal}) AS similarity_score
            FROM breads
            WHERE "isAvailable" = true
            AND embedding IS NOT NULL
            AND id NOT IN ({exclude_str})
            AND 1 - (embedding <=> {vector_literal}) >= :min_sim
            {category_clause}
            ORDER BY embedding <=> {vector_literal}
            LIMIT :top_k
        """)

        params: dict = {"min_sim": min_similarity, "top_k": top_k}
        if category_filter:
            params["category"] = category_filter

        result = await self.db.execute(sql, params)
        rows = result.fetchall()

        return [
            {
                "id": row.id,
                "name": row.name,
                "category": row.category,
                "price": float(row.price) if row.price is not None else None,
                "image_url": row.image_url,
                "gojek_url": row.gojek_url,
                "grab_url": row.grab_url,
                "shopee_food_url": row.shopee_food_url,
                "similarity_score": round(float(row.similarity_score), 4),
            }
            for row in rows
        ]