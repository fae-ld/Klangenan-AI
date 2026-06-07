-- ============================================================
-- Migration: Setup pgvector untuk tabel breads
-- Jalankan SEKALI setelah Prisma migration membuat tabel breads
-- ============================================================

-- 1. Aktifkan ekstensi pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Tambah kolom embedding ke tabel breads
--    (Prisma tidak support tipe vector native, jadi ditambah manual)
ALTER TABLE breads
ADD COLUMN IF NOT EXISTS embedding vector(384);

-- 3. HNSW index untuk cosine similarity search
CREATE INDEX IF NOT EXISTS breads_embedding_hnsw_idx
ON breads
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 4. Verifikasi
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'breads'
  AND indexname LIKE '%embedding%';