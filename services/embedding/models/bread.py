"""
ORM Model: Bread
 
Tabel ini di-share antara Next.js (via Prisma) dan FastAPI (via SQLAlchemy).
FastAPI hanya READ + UPDATE kolom `embedding` — DDL dikelola Prisma.
 
Prisma schema mapping:
  Bread.imageUrl      → image_url      (camelCase → snake_case)
  Bread.imagePublicId → image_public_id
  Bread.isAvailable   → is_available
  Bread.gojekUrl      → gojek_url
  Bread.grabUrl       → grab_url
  Bread.shopeeFoodUrl → shopee_food_url
  Bread.createdAt     → created_at
  Bread.updatedAt     → updated_at
"""

from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqalchemy.orm import Mapped,mapped_column

from ..database.base import Base

# Harus sama dengan dimensi model sentence-transformers yang dipakai.
# paraphrase-multilingual-MiniLM-L12-v2 → 384 dimensi
EMBEDDING_DIM = 384

class Bread(Base):
    __tablename__ = "breads"
    
    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    
    id : Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True)
    
    #------------------------------------------------------------------
    # Kolom konten (dikelola Prisma / Next.js)
    # ------------------------------------------------------------------
    name : Mapped[str] = mapped_column(String(255),nullable=False)
    category : Mapped[str] = mapped_column(String(100),nullable=False)
    description : Mapped[Optional[str]] = mapped_column(Text,nullable=True)
    price: Mapped[Optional[float]] = mapped_column(Float,nullable=True)
    
    #Cloudinary
    image_url : Mapped[Optional[str]] = mapped_column("imageUrl",Text,nullable=True)
    image_public_id : Mapped[Optional[str]] = mapped_column("imagePublicId",Text,nullable=True)
    
    # marketplace links
    gojek_url: Mapped[Optional[str]] = mapped_column("gojekUrl", Text, nullable=True)
    grab_url: Mapped[Optional[str]] = mapped_column("grabUrl", Text, nullable=True)
    shopee_food_url: Mapped[Optional[str]] = mapped_column(
        "shopeeFoodUrl", Text, nullable=True
    )
    
    is_available: Mapped[bool] = mapped_column(
        "isAvailable", Boolean, default=True, nullable=False
    )
    
    # ------------------------------------------------------------------
    # Kolom embedding (dikelola FastAPI)
    # ------------------------------------------------------------------
    embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(EMBEDDING_DIM), nullable=True,comment="84-dim sentence-transformers embedding untuk similarity search")
    
    # ------------------------------------------------------------------
    # Timestamps (dikelola Prisma)
    # ------------------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column("createdAt", DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column("updatedAt", DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self)->str:
        has_embedding = self.embedding is not None
        return f"<Bread id={self.id} name='{self.name}' category='{self.category}' embedding={'Yes' if has_embedding else 'No'}>"