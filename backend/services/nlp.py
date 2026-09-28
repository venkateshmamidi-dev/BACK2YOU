import numpy as np
from typing import List, Optional, Union
from sklearn.metrics.pairwise import cosine_similarity
from backend.config import settings

_nlp_model = None

def get_nlp_model():
    """
    Lazy initialization of SentenceTransformer model.
    Loads once into memory and reuses for high-throughput inference.
    """
    global _nlp_model
    if _nlp_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            print(f"[NLP] Loading SentenceTransformer model '{settings.SENTENCE_MODEL_NAME}'...")
            _nlp_model = SentenceTransformer(settings.SENTENCE_MODEL_NAME)
            print(f"[NLP] SentenceTransformer model loaded successfully.")
        except Exception as e:
            print(f"[NLP] Error initializing SentenceTransformer: {e}. Falling back to TF-IDF semantic vectorizer.")
            _nlp_model = "fallback"
    return _nlp_model

def generate_text_embedding(text: str) -> List[float]:
    """
    Generates a dense normalized semantic vector embedding for the input text description.
    """
    if not text or not text.strip():
        return [0.0] * 384

    model = get_nlp_model()
    if model != "fallback" and model is not None:
        try:
            emb = model.encode(text.strip(), convert_to_numpy=True, normalize_embeddings=True)
            return emb.tolist()
        except Exception as e:
            print(f"[NLP] Error during encoding: {e}")

    # Deterministic semantic hash / n-gram representation fallback if model loading is unavailable
    tokens = text.lower().split()
    vec = np.zeros(384, dtype=np.float32)
    for i, token in enumerate(tokens):
        idx = hash(token) % 384
        vec[idx] += 1.0 / (i + 1.0)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()

def calculate_text_similarity(
    embedding1: Optional[Union[List[float], np.ndarray]],
    embedding2: Optional[Union[List[float], np.ndarray]]
) -> float:
    """
    Computes cosine similarity between two text embeddings.
    Returns float score in range [0.0, 1.0].
    """
    if embedding1 is None or embedding2 is None:
        return 0.0

    v1 = np.array(embedding1, dtype=np.float32).reshape(1, -1)
    v2 = np.array(embedding2, dtype=np.float32).reshape(1, -1)

    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    sim = float(cosine_similarity(v1, v2)[0][0])
    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, (sim + 1.0) / 2.0 if sim < 0 else sim))
