"""
GeminiLLM — implementasi BaseLLM menggunakan Google Gemini Flash.
 
Model default: gemini-2.0-flash (gratis, generous rate limit)
Docs: https://ai.google.dev/api/generate-content
"""

import google.generativeai as genai

from ..config import settings
from .base import BaseLLM, ChatContext, Message

class GeminiLLM(BaseLLM):
    MODEL_NAME = settings.MODEL_NAME
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(self.MODEL_NAME)
    
    async def chat(self,
                   messages : list[Message],
                   context: ChatContext) -> str:
        """
        Kirim pesan ke Gemini Flash dengan konteks RAG di system prompt.
 
        Flow:
        1. Build system prompt berisi data roti relevan
        2. Convert history messages ke format Gemini
        3. Kirim ke Gemini API
        4. Return response text
        """
        
        system_promt = self.build_system_prompt(context)
        
        # Gemini menggunakan format {role,parts} bukan {role,content}
        # role hanya boleh "user" atau "model"
        history = []
        for msg in messages[:-1]: # semua kecuali pesan akhir menjadi history
            role = "model" if msg.role == "assistant" else "user"
            history.append({
                "role" : role,
                "parts": [msg.content]
            })
            
        # pesan terakhir = pertanyaan user saat ini
        current_message = messages[-1].content 
        
        # start chat dengan history
        chat_session = self.model.start_chat(history=history)
        
        # inject system promt ke pesan utama kalau history kosong
        # atau kirim sebagai context tambahan
        prompt = f"{system_promt}\n\nPertanyaan pelanggan: {current_message}"
        
        response = await chat_session.send_message_async(prompt) 
        return response.text
        
    