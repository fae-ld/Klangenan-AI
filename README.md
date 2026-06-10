# 🥖 Klangenan AI — Microservice

AI microservice untuk **Klangenan Roti Shop** yang menangani embedding produk, rekomendasi berbasis semantic similarity, dan chatbot RAG menggunakan `sentence-transformers`, `pgvector`, dan LLM provider yang dapat diganti.

---

## Tech Stack

| Layer | Teknologi |
|---|---|
| Framework | FastAPI (Python) |
| Embedding Model | `sentence-transformers` (paraphrase-multilingual-MiniLM-L12-v2) |
| Database | PostgreSQL + pgvector (Supabase) |
| ORM | SQLAlchemy (async) |
| Driver | asyncpg |
| LLM Default | Google Gemini Flash |
| LLM Alternatif | Ollama (lokal) |
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
        ├── llm/
        │   ├── base.py              # Abstract interface + system prompt builder
        │   ├── gemini.py            # Implementasi Google Gemini Flash
        │   ├── ollama.py            # Implementasi Ollama (local LLM)
        │   └── factory.py           # Baca LLM_PROVIDER dari .env → return instance
        │
        └── routes/
            ├── embed.py             # POST /embed/bread, POST /embed/bread/batch
            ├── recommend.py         # POST /recommend
            └── chat.py              # POST /chat (RAG chatbot)
```

---

## Endpoints

### Health Check

```
GET /
```

```json
{
  "status": "ok",
  "message": "Klangenan AI is running 🎯",
  "llm_provider": "gemini"
}
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
  "model": "paraphrase-multilingual-MiniLM-L12-v2"
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
- Ganti model sentence-transformers ke versi baru

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

### Chatbot (RAG)

```
POST /api/v1/chat/
```

Chatbot dengan RAG pipeline — pertanyaan user di-embed, roti yang relevan diambil dari pgvector, lalu dikirim sebagai konteks ke LLM.

**Request:**
```json
{
  "message": "ada yang rasa stroberi ga?",
  "history": [
    { "role": "user", "content": "halo, lagi buka?" },
    { "role": "assistant", "content": "Halo! Selamat datang di Klangenan Roti Shop! Ada yang bisa saya bantu?" },
    { "role": "user", "content": "mau cari roti buat sarapan nih" },
    { "role": "assistant", "content": "Untuk sarapan kami punya banyak pilihan! Ada yang suka manis atau gurih?" },
    { "role": "user", "content": "manis aja" },
    { "role": "assistant", "content": "Untuk yang manis ada Roti Coklat Keju, Roti Krim Vanilla, dan beberapa pilihan lainnya!" }
  ],
  "top_k_context": 3,
  "min_similarity": 0.3
}
```

**Response:**
```json
{
  "reply": "Untuk rasa stroberi, kami punya Roti Stroberi Krim seharga Rp 12.000! Tersedia di GoFood dan GrabFood. Mau langsung pesan?",
  "context_used": ["Roti Stroberi Krim", "Roti Buah Segar", "Roti Selai Stroberi"]
}
```

**Field penjelasan:**

| Field | Keterangan |
|---|---|
| `message` | Pertanyaan user saat ini |
| `history` | Riwayat percakapan — selalu bergantian `user → assistant` |
| `top_k_context` | Jumlah roti yang diambil sebagai konteks RAG (default: 3) |
| `min_similarity` | Threshold similarity untuk RAG — lebih rendah dari recommend agar konteks lebih luas (default: 0.3) |
| `reply` | Jawaban dari LLM |
| `context_used` | Nama roti yang dijadikan konteks — berguna untuk debugging |

---

## Inisialisasi

### 1. Clone & Install Dependencies

```bash
git clone <repo-url>
cd klangenan-AI

uv sync
```

### 2. Setup Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:
```env
# DATABASE — driver WAJIB asyncpg
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/DBNAME
DB_ECHO=false

# APP
DEBUG=false
APP_NAME=Klangenan AI Microservice
ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# LLM — pilih provider
LLM_PROVIDER=gemini

# Gemini (aktif kalau LLM_PROVIDER=gemini)
GEMINI_API_KEY=your_gemini_api_key_here

# Ollama (aktif kalau LLM_PROVIDER=ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

> Untuk Supabase, format DATABASE_URL:
> `postgresql+asyncpg://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres`

> Dapatkan Gemini API key gratis di: https://aistudio.google.com/app/apikey

### 3. Setup Database

Pastikan tabel `breads` sudah dibuat oleh Prisma migration dari Next.js terlebih dahulu, lalu jalankan:

```bash
psql "postgresql://USER:PASSWORD@HOST:5432/DBNAME" \
  -c "CREATE EXTENSION IF NOT EXISTS vector" \
  -c "ALTER TABLE breads ADD COLUMN IF NOT EXISTS embedding vector(384)" \
  -c "CREATE INDEX IF NOT EXISTS breads_embedding_hnsw_idx ON breads USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
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
# Aktifkan virtual environment
.venv\Scripts\Activate.ps1     # Windows PowerShell
source .venv/bin/activate       # Linux/macOS

# Jalankan dari root project
python -m uvicorn main:app --reload --port 8000
```

Server berjalan di `http://localhost:8000`  
Swagger UI tersedia di `http://localhost:8000/docs`

### 6. Embed Semua Roti (Pertama Kali)

```bash
curl -X POST http://localhost:8000/api/v1/embed/bread/batch
```

---

## Ganti LLM Provider

Untuk ganti model, cukup ubah **satu baris** di `.env` tanpa mengubah kode apapun:

```env
# Pakai Gemini Flash (cloud, gratis tier generous)
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key

# Pakai Ollama (lokal, fully gratis, butuh min 8GB RAM)
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:7b
```

Provider yang tersedia:

| Provider | Keterangan | Biaya |
|---|---|---|
| `gemini` | Google Gemini Flash via API | Gratis (rate limited) |
| `ollama` | Local LLM via Ollama | Gratis (butuh GPU/RAM) |

---

## Integrasi dengan Next.js

Tambahkan di `.env` Next.js:
```env
AI_SERVICE_URL=http://localhost:8000/api/v1
```

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

// Rekomendasi di halaman detail roti
const res = await fetch(`${process.env.AI_SERVICE_URL}/recommend/`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ bread_id: id, top_k: 4 }),
  next: { revalidate: 300 },
});

// Chatbot — kelola history di state frontend
const [history, setHistory] = useState([]);

async function sendMessage(userMessage: string) {
  const res = await fetch(`${process.env.AI_SERVICE_URL}/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: userMessage,
      history: history,
      top_k_context: 3,
      min_similarity: 0.3,
    }),
  });

  const data = await res.json();

  setHistory(prev => [
    ...prev,
    { role: "user", content: userMessage },
    { role: "assistant", content: data.reply },
  ]);
}
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

- Microservice ini **tidak mengelola DDL** — semua schema dikelola Prisma dari Next.js, kecuali kolom `embedding` yang ditambah manual via `migrations.sql`.
- Embedding model dan LLM di-load sekali saat startup dan di-share ke semua request via `app.state`.
- pgvector menggunakan **HNSW index** untuk cosine similarity search yang efisien.
- RAG chatbot menggunakan `min_similarity: 0.3` (lebih rendah dari recommend `0.5`) agar konteks yang diambil lebih luas untuk percakapan natural.
