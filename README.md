# 🥖 Klangenan AI — Microservice

AI microservice untuk **Klangenan Roti Shop** yang menangani embedding produk dan rekomendasi berbasis semantic similarity menggunakan `sentence-transformers` dan `pgvector`.

---

## Tech Stack

| Layer | Teknologi |
|---|---|
| Framework | FastAPI (Python) |
| Embedding Model | `sentence-transformers` (all-MiniLM-L6-v2) |
| Database | PostgreSQL + pgvector (Supabase) |
| ORM | SQLAlchemy (async) |
| Driver | asyncpg |
| Package Manager | uv |

---

## Struktur Project

```
klangenan-AI/
├── main.py                          # Entry point FastAPI
├── .env                             # Environment variables (tidak di-commit)
├── .env.example                     # Template environment variables
├── pyproject.toml                   # Dependencies (dikelola uv)
│
└── services/
    └── embedding/
        ├── config.py                # Settings via pydantic-settings
        ├── model.py                 # EmbeddingModel (sentence-transformers)
        │
        ├── database/
        │   ├── base.py              # DeclarativeBase SQLAlchemy
        │   ├── connection.py        # Engine + AsyncSession + get_db dependency
        │   └── migrations.sql       # SQL setup pgvector (jalankan sekali)
        │
        ├── llm/
        │   ├──factory.py            # mengambil llm (sesuai dengan env)
        │   ├──base.py               # abstraksi untuk LLM
        │   ├──gemini.py             # Penerapan untuk Gemini
        |   └──ollama.py             # penerapan untuk ollama
        ├── models/
        │   └── bread.py             # ORM model tabel breads + kolom embedding
        │
        ├── repositories/
        │   └── bread_repository.py  # Semua query DB (CRUD + similarity search)
        │
        └── routes/
            ├── embed.py             # POST /embed/bread, POST /embed/bread/batch
            └── recommend.py         # POST /recommend
```

---

## Endpoints

### Health Check
```
GET /
```
```json
{ "status": "ok", "message": "Klangenan AI is running 🎯" }
```

---

### Embedding

#### Embed Satu Roti
```
POST /api/v1/embed/bread
```

**Request:**
```json
{
  "bread_id": 1,
  "name": "Roti Coklat Keju",
  "category": "Manis",
  "description": "Roti lembut dengan isian coklat dan keju mozzarella",
  "normalize": true
}
```

**Response:**
```json
{
  "bread_id": 1,
  "saved": true,
  "text_input": "nama: Roti Coklat Keju | kategori: Manis | deskripsi: ...",
  "dimension": 384,
  "model": "all-MiniLM-L6-v2"
}
```

> Dipanggil saat admin **CREATE** atau **UPDATE** nama/kategori/deskripsi roti.
> Tidak perlu dipanggil saat update harga, stok, gambar, atau URL marketplace.

---

#### Bulk Embed (Batch)
```
POST /api/v1/embed/bread/batch
```

Embed semua roti yang belum punya embedding. Berguna saat:
- Pertama kali setup (data sudah ada di DB tapi belum di-embed)
- Ganti model ke versi baru

**Response:**
```json
{
  "message": "Berhasil embed 12 dari 12 roti",
  "processed": 12,
  "failed": []
}
```

---

### Rekomendasi

```
POST /api/v1/recommend/
```

**Request:**
```json
{
  "bread_id": 1,
  "top_k": 5,
  "min_similarity": 0.5,
  "category_filter": null,
  "exclude_ids": []
}
```

**Response:**
```json
{
  "source_bread_id": 1,
  "recommendations": [
    {
      "id": 3,
      "name": "Roti Coklat Almond",
      "category": "Manis",
      "price": 15000,
      "image_url": "https://res.cloudinary.com/...",
      "gojek_url": "https://gofood.co.id/...",
      "grab_url": null,
      "shopee_food_url": null,
      "similarity_score": 0.9123
    }
  ],
  "total": 1
}
```

> `similarity_score` berkisar antara `0.0` (tidak mirip) hingga `1.0` (identik).
> Gunakan `min_similarity: 0.0` untuk mendapatkan semua hasil tanpa threshold.

---

## Inisialisasi

### 1. Clone & Install Dependencies

```bash
# Clone project
git clone <repo-url>
cd klangenan-AI

# Install dependencies via uv
uv sync
```

### 2. Setup Environment Variables

```bash
# Copy template
cp .env.example .env
```

Edit `.env`:
```env
# Driver WAJIB asyncpg (bukan psycopg2)
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DBNAME

DB_ECHO=false
DEBUG=false
APP_NAME=Klangenan AI Microservice
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
```

> Untuk Supabase, format URL-nya:
> `postgresql+asyncpg://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres`

### 3. Setup Database

Pastikan tabel `breads` sudah dibuat oleh Prisma migration dari Next.js terlebih dahulu, lalu jalankan:

```bash
# Tambah kolom embedding + HNSW index di PostgreSQL
psql "postgresql://USER:PASSWORD@HOST:5432/DBNAME" -c "CREATE EXTENSION IF NOT EXISTS vector" -c "ALTER TABLE breads ADD COLUMN IF NOT EXISTS embedding vector(384)" -c "CREATE INDEX IF NOT EXISTS breads_embedding_hnsw_idx ON breads USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
```

Atau gunakan file SQL (pastikan terminal encoding UTF-8):
```bash
psql "CONNECTION_STRING" -f services/embedding/database/migrations.sql
```

### 4. Tambah Kolom Embedding di Prisma Schema

Agar kolom `embedding` tidak terhapus saat `prisma migrate`:

```prisma
model Bread {
  // ... kolom lainnya
  embedding Unsupported("vector(384)")?

  @@map("breads")
}
```

### 5. Jalankan Server

```bash
# Aktifkan virtual environment dulu
.venv\Scripts\Activate.ps1          # Windows PowerShell
source .venv/bin/activate            # Linux/macOS

# Jalankan dari root project
python -m uvicorn main:app --reload --port 8000
```

Server berjalan di `http://localhost:8000`
Swagger UI tersedia di `http://localhost:8000/docs`

### 6. Embed Semua Roti (Pertama Kali)

Setelah server berjalan, hit endpoint batch untuk embed semua roti yang ada di DB:

```bash
curl -X POST http://localhost:8000/api/v1/embed/bread/batch
```

---

## Integrasi dengan Next.js

Tambahkan di `.env` Next.js:
```env
AI_SERVICE_URL=http://localhost:8000/api/v1
```

Contoh pemanggilan dari Next.js Route Handler:
```typescript
// Embed roti baru setelah INSERT ke DB
await fetch(`${process.env.AI_SERVICE_URL}/embed/bread`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    bread_id: newBread.id,
    name: newBread.name,
    category: newBread.category,
    description: newBread.description ?? "",
  }),
});

// Ambil rekomendasi di halaman detail roti
const res = await fetch(`${process.env.AI_SERVICE_URL}/recommend/`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ bread_id: id, top_k: 4 }),
  next: { revalidate: 300 }, // cache 5 menit
});
```

---

## Kapan Re-embed Diperlukan?

| Aksi | Perlu Re-embed? |
|---|---|
| Update nama / kategori / deskripsi | ✅ Ya |
| Update harga / stok | ❌ Tidak |
| Update gambar / URL marketplace | ❌ Tidak |
| Ganti model sentence-transformers | ✅ Ya — jalankan `/embed/bread/batch` |

---

## Catatan

- Microservice ini **tidak mengelola DDL** (CREATE TABLE, ALTER TABLE) — semua schema dikelola Prisma dari Next.js, kecuali kolom `embedding` yang ditambah manual via `migrations.sql`.
- Model embedding di-load sekali saat startup dan di-share ke semua request via `app.state.embedding_model`.
- pgvector menggunakan **HNSW index** untuk cosine similarity search yang efisien.
