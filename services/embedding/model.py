from sentence_transformers import SentenceTransformer
from typing import List,Optional
import numpy as np
from dotenv import load_dotenv

load_dotenv()

class EmbeddingModel:
    """
    Wrapper untuk SentenceTransformer.
    Model dimuat sekali saat startup dan di-reuse untuk semua request.

    Default model: 'paraphrase-multilingual-MiniLM-L12-v2'
    - Mendukung Bahasa Indonesia dengan baik
    - Output: 384-dimensional vector per teks
    - Ringan dan cepat

    Alternatif:
    - 'all-MiniLM-L6-v2'          → lebih cepat, tapi kurang akurat untuk non-English
    - 'paraphrase-multilingual-mpnet-base-v2' → lebih akurat, lebih berat
    """
    
    MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
    
    def __init__(self):
        self.model = SentenceTransformer(self.MODEL_NAME)
        self.dimension = self.model.get_sentence_embedding_dimension()
    
    @staticmethod
    def build_product_text(
        name: str,
        category: str,
        description: Optional[str] = None,
    ) -> str:
        """
        Gabungkan field produk menjadi 1 string terstruktur.

        Format: "nama: X | kategori: Y | deskripsi: Z"
        Jika description null, field deskripsi tidak disertakan.

        Label eksplisit ("nama:", "kategori:") membantu model memahami
        konteks setiap field sehingga representasi semantiknya lebih akurat.
        """
        
        parts = [
            f"nama: {name.strip()}",
            f"kategori: {category.strip()}",
        ]
        
        if description:
            parts.append(f"deskripsi: {description.strip()}")
            
        return " | ".join(parts)
    
    def encode_single(self,text: str, normalize:bool = True) -> List[float]:
        """
        Encode 1 string menjadi 1 vector embedding.

        Args:
            text: String yang ingin di-embed
            normalize: Normalisasi ke unit length (untuk cosine similarity)

        Returns:
            List of float, panjang = self.dimension
        """
        
        embedding = self.model.encode(
            text,
            normalize_embeddings=normalize,
            show_progress_bar=False,
        )
        return embedding.tolist()
    
    @staticmethod
    def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """
        Hitung cosine similarity antara 2 vector.
        Jika kedua vector sudah dinormalisasi (normalize=True),
        cukup dot product — hasilnya sama dan lebih cepat.

        Returns:
            float antara -1 dan 1. Semakin dekat ke 1, semakin mirip.
        """
        a = np.array(vec_a)
        b = np.array(vec_b)
        
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(np.dot(a,b)/(norm_a * norm_b))
    
    
    @staticmethod
    def interpret_similarity(score: float) -> str:
        """Terjemahkan score cosine similarity ke bahasa manusia."""
        if score >= 0.90:
            return "Sangat mirip"
        elif score >= 0.75:
            return "Mirip"
        elif score >= 0.50:
            return "Cukup mirip"
        elif score >= 0.25:
            return "Sedikit mirip"
        else:
            return "Tidak mirip"

        
    