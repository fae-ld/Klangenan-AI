CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE breads
ADD COLUMN IF NOT EXISTS embedding vector(384);

CREATE INDEX IF NOT EXISTS breads_embedding_hnsw_idx
ON breads
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'breads'
AND indexname LIKE '%embedding%';