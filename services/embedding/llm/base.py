
"""
BaseLLM — abstract interface untuk semua LLM provider.
 
Semua provider (Gemini, Ollama, Claude, OpenAI) harus implement
method chat() dengan signature yang sama.
 
Dengan pola ini, route chatbot tidak perlu tahu model apa yang dipakai —
cukup panggil llm.chat() dan hasilnya sama.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Message:
    role: str # "user" | "assistant" | "system"
    content: str
    
@dataclass
class ChatContext:
    """Konteks RAG yang sudah diambil dari pgvector"""
    breads : list[dict] # list roti yang releevan dengan pertanyaan user
    query: str # pertanyaan user asli, untuk diproses LLM
    
class BaseLLM(ABC):
    """inteface untuk semua LLM provider (Gemini, Ollama, Claude, OpenAI)"""
    
    @abstractmethod
    async def chat(self, messages: list[Message], context: ChatContext) -> str:
        """
        kirim pesan ke LLM dan kembalikan response sebagai string
        
        Args:
            messages: riwayat percakapan (termasuk pesan user baru)
            context: konteks RAG yang berisi informasi terkait pertanyaan user
            
        Returns:
            response dari LLM sebagai string
        """
        ...
    
    def build_system_prompt(self, context: ChatContext) -> str:
        """
        Build system prompt dengan konteks RAG.
        Shared oleh semua provider — bisa di-override jika perlu.
        """
        bread_list = ""
        if context.breads:
            for i, bread in enumerate(context.breads, 1):
                price = f"Rp {int(bread['price']):,}" if bread.get("price") else "Hubungi toko"
                availability = "Tersedia" if bread.get("is_available", True) else "Habis"
                marketplace = []
                if bread.get("gojek_url"):
                    marketplace.append("GoFood")
                if bread.get("grab_url"):
                    marketplace.append("GrabFood")
                if bread.get("shopee_food_url"):
                    marketplace.append("ShopeeFood")
                marketplace_str = ", ".join(marketplace) if marketplace else "Kunjungi toko langsung"
 
                bread_list += f"""
{i}. {bread['name']}
   - Kategori : {bread.get('category', '-')}
   - Harga    : {price}
   - Status   : {availability}
   - Beli di  : {marketplace_str}
   - Deskripsi: {bread.get('description') or 'Tidak ada deskripsi'}
"""
        else:
            bread_list = "Tidak ada produk yang relevan ditemukan."
 
        return f"""Kamu adalah asisten virtual untuk Klangenan Roti Shop, sebuah toko roti artisan yang menjual berbagai jenis roti berkualitas tinggi.
 
Tugasmu adalah membantu pelanggan dengan ramah dan informatif dalam Bahasa Indonesia.
 
Kamu bisa membantu pelanggan untuk:
- Mencari dan merekomendasikan roti yang sesuai kebutuhan mereka
- Memberikan informasi harga dan ketersediaan produk
- Menjelaskan bahan dan deskripsi produk
- Mengarahkan cara pembelian (GoFood, GrabFood, ShopeeFood)
 
PRODUK YANG RELEVAN DENGAN PERTANYAAN PELANGGAN:
{bread_list}
 
PANDUAN MENJAWAB:
- Gunakan data produk di atas sebagai acuan utama
- Jika produk yang dicari tidak ada dalam daftar, sampaikan dengan sopan dan tawarkan alternatif yang tersedia
- Jawab dengan singkat, ramah, dan to the point
- Jangan mengarang informasi produk yang tidak ada dalam daftar
- Selalu sebutkan harga dan cara pembelian jika relevan
- Gunakan Bahasa Indonesia yang baik dan benar

Negative prompt (jangan lakukan ini):
- Jangan menyebutkan bahwa kamu adalah AI atau asisten virtual
- Jangan memberikan informasi yang tidak ada dalam daftar produk di atas
- Jangan menggunakan kata-kata kasar
- jangan jawab pertanyaan apabila tidak berhubungan dengan pemesanan roti pada Klangenan
- Jangan mention brand lain dan jangan jawab pertanyaan apabila menyangkut brand lain selain Klangenan
"""
