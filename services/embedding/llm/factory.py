"""
LLMFactory — baca LLM_PROVIDER dari .env dan return instance yang tepat.
 
Untuk ganti model, cukup ubah .env:
    LLM_PROVIDER=gemini   → GeminiLLM
    LLM_PROVIDER=ollama   → OllamaLLM
 
Tidak perlu ubah kode apapun selain .env.
"""

from ..config import settings
from .base import BaseLLM

def get_llm() -> BaseLLM:
    """
    Factory function — return LLM instance sesuai LLM_PROVIDER di .env.
    Dipanggil sekali saat startup, disimpan di app.state.llm.
    """
    
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "gemini":
        from .gemini import GeminiLLM
        return GeminiLLM()
    elif provider == "ollama":
        from .ollama import OllamaLLM
        return OllamaLLM()
    
    else:
        raise ValueError(
            f"LLM_PROVIDER '{provider}' tidak dikenal. "
            "Pilihan yang tersedia: gemini, ollama"
        )