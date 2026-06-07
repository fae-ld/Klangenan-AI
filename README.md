# Klangenan AI 🎯

Microservice AI berbasis **FastAPI** + **sentence-transformers**.

## Struktur Proyek

```
KLANGENAN-AI/
├── main.py
├── pyproject.toml
├── services/
│   └── embedding/
│       ├── model.py       ← EmbeddingModel: build_product_text, encode_single, cosine_similarity
│       ├── router.py      ← Endpoints: /product, /similarity, /info
│       └── schemas.py     ← Pydantic: ProductEmbedRequest, SimilarityRequest, dst
```

## Setup

```bash
pip install -e .
uvicorn main:app --reload
```

## Endpoints

| Method | Path | Deskripsi |
|--------|------|-----------|
| GET | `/` | Health check |
| POST | `/api/v1/embedding/product` | Embed 1 produk → 1 vector |
| POST | `/api/v1/embedding/similarity` | Cosine similarity 2 produk |
| GET | `/api/v1/embedding/info` | Info model aktif |

---

## Contoh: Embed Produk Baru

```bash
POST /api/v1/embedding/product
{
  "name": "Roti Coklat Lembut",
  "category": "Roti Manis",
  "description": "Roti lembut dengan isian coklat premium."
}
```

Response:
```json
{
  "embedding": [0.12, -0.34, ...],   // 384 angka
  "text_input": "nama: Roti Coklat Lembut | kategori: Roti Manis | deskripsi: ...",
  "dimension": 384,
  "model": "paraphrase-multilingual-MiniLM-L12-v2"
}
```

---

## Contoh: Cek Kemiripan 2 Produk

```bash
POST /api/v1/embedding/similarity
{
  "product_a": { "name": "Roti Coklat", "category": "Roti Manis" },
  "product_b": { "name": "Roti Keju",   "category": "Roti Manis" }
}
```

Response:
```json
{ "score": 0.8712, "interpretation": "Mirip" }
```

---

## Integrasi pgvector (Prisma)

### 1. Schema Prisma

```prisma
// Tambah field embedding di model produk
model Product {
  id          String   @id @default(cuid())
  name        String
  category    String
  description String?
  embedding   Unsupported("vector(384)")?  // pgvector

  @@index([embedding], type: Hnsw(m: 16, efConstruction: 64), opclass: vector_cosine_ops)
}
```

### 2. Simpan vector saat CREATE/UPDATE

```typescript
// Di service/controller produk kamu
async function upsertProduct(data: ProductInput) {
  // 1. Embed via microservice
  const res = await fetch("http://localhost:8000/api/v1/embedding/product", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const { embedding } = await res.json();

  // 2. Simpan ke DB
  await prisma.$executeRaw`
    INSERT INTO "Product" (id, name, category, description, embedding)
    VALUES (${cuid()}, ${data.name}, ${data.category}, ${data.description},
            ${JSON.stringify(embedding)}::vector)
    ON CONFLICT (id) DO UPDATE
      SET embedding = EXCLUDED.embedding;
  `;
}
```

### 3. Query rekomendasi (cosine similarity)

```typescript
async function getRecommendations(productId: string, limit = 10) {
  // Ambil embedding produk yang sedang dilihat
  const product = await prisma.product.findUnique({ where: { id: productId } });

  // Cari N produk terdekat via pgvector
  const similar = await prisma.$queryRaw`
    SELECT id, name, category,
           1 - (embedding <=> ${product.embedding}::vector) AS similarity
    FROM "Product"
    WHERE id != ${productId}
    ORDER BY embedding <=> ${product.embedding}::vector
    LIMIT ${limit};
  `;

  return similar;
}
```

---

## Docs Interaktif

Buka **http://localhost:8000/docs** setelah server jalan.
