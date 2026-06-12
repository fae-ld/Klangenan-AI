"""
OllamaLLM — implementasi BaseLLM menggunakan Ollama (local).
 
Setup Ollama:
1. Install: https://ollama.com/download
2. Pull model: ollama pull qwen2.5:7b
3. Pastikan Ollama running: ollama serve
4. Set di .env: LLM_PROVIDER=ollama, OLLAMA_MODEL=qwen2.5:7b
 
Model yang direkomendasikan untuk Bahasa Indonesia:
- qwen2.5:7b  — terbaik untuk konten Asia, butuh ~8GB RAM
- qwen2.5:3b  — lebih ringan, ~4GB RAM
- llama3.2:3b — alternatif ringan
"""

import httpx

from ..config import settings
from .base import BaseLLM,ChatContext,Message

class OllamaLLM(BaseLLM):
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        
    async def chat(
        self,
        messages : list[Message],
        context : ChatContext
    ) -> str:
        """
        Kirim pesan ke Ollama local server.
        Menggunakan /api/chat endpoint (OpenAI-compatible).
        """
        
        system_prompt = self.build_system_prompt(context)
        
        # Format messages untuk Ollama (OPENAI-compatible)
        ollama_messages = [{"role":"system","content":system_prompt}] 
        for msg in messages:
            ollama_messages.append({
                "role" : msg.role,
                "content" : msg.content
            })     
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json= {
                    "model" : self.model,
                    "messages" : ollama_messages,
                    "stream" : False,
                    "options" : {
                        "temperature" : 0.7,
                        "num_predict" : 512
                    }
                }
            )
            
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]