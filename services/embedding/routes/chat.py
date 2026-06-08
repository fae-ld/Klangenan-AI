"""
Route: /chat
 
Chatbot endpoint dengan RAG pipeline:
1. Terima pesan user + history percakapan
2. Embed pertanyaan user → vector
3. Query pgvector → ambil roti yang relevan (similarity search)
4. Inject konteks roti ke system prompt
5. Kirim ke LLM → return response
 
Flow ini memastikan jawaban selalu berdasarkan data produk terbaru di DB.
"""

from fastapi import APIRouter, Depends,HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import get_db
from ..llm.base import ChatContext, Message
from ..repositories.bread_repository import BreadRepository

router = APIRouter(prefix="/chat",tags=["Chatbot"])

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role : str = Field(...,pattern="^(user|assistant)$")
    content : str

class ChatRequest(BaseModel):
    message : str # pesan user saat ini
    history : list[ChatMessage] = [] # riwayat percakapan sebelumnya
    top_k_context : int = 3 # berapa roti yang diambil sebagai konteks
    min_similarity : float = 0.3 # threshold lebih rendah dari recommend
                                 # agar konteks lebih luas untuk chatbot
                                 
class ChatResponse(BaseModel):
    reply : str # Jawaban LLM
    context_used : list[str] # nama roti yang dijadikan context
    
 
# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model= ChatResponse,
    summary="Chat dengan asisten Klangenan",
)
async def chat(
    request: Request,
    body : ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Chatbot RAG — jawaban berdasarkan data produk real-time dari database.
 
    **Contoh pertanyaan yang bisa dijawab:**
    - "Ada roti coklat?"
    - "Rekomendasikan roti untuk sarapan"
    - "Berapa harga croissant?"
    - "Roti apa yang bisa dipesan lewat GoFood?"
    """
    
    embedding_model = request.app.state.embedding_model
    llm = request.app.state.llm
    repo = BreadRepository(db)
    
    # ------------------------------------------------------------------
    # Step 1: Embed pertanyaan user
    # ------------------------------------------------------------------
    try: 
        query_embedding = embedding_model.encode_single(
            body.message,
            normalize = True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"gagal embed pertanyaan {e}")
    
    # ------------------------------------------------------------------
    # Step 2: RAG — ambil roti yang relevan dari pgvector
    # ------------------------------------------------------------------
    relevant_breads = await repo.find_similar(
        source_embedding=query_embedding,
        exclude_ids=[],
        top_k=body.top_k_context,
        min_similarity=body.min_similarity
    )
    
    # ------------------------------------------------------------------
    # Step 3: Build context + history untuk LLM
    # ------------------------------------------------------------------
    context = ChatContext(
        breads=relevant_breads,
        query=body.message
    )
    
    # Convert history ke format internal Message
    messages = [
        Message(role=msg.role, content=msg.content)
        for msg in body.history
    ]
    
    # tambahkan pesan user saat ini ke akhir
    messages.append(Message(role="user",content=body.message))
    
    # ------------------------------------------------------------------
    # Step 4: Kirim ke LLM
    # ------------------------------------------------------------------
    try:
        reply = await llm.chat(messages=messages,context=context)
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Gagal mendapat response LLM: {e}")
    
    return ChatResponse(
        reply=reply,
        context_used=[b["name"] for b in relevant_breads]
    )