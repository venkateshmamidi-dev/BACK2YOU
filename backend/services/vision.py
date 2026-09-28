import os
import io
import numpy as np
from typing import List, Optional, Union
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
import torch
import torchvision.transforms as transforms
from backend.config import settings

_vision_model = None
_vision_transform = None

def get_vision_model():
    """
    Lazy initialization of pretrained Computer Vision feature extractor.
    Uses MobileNetV3-Small / ResNet pretrained on ImageNet for efficient CPU feature extraction.
    """
    global _vision_model, _vision_transform
    if _vision_model is None:
        try:
            from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights
            weights = MobileNet_V3_Small_Weights.DEFAULT
            model = mobilenet_v3_small(weights=weights)
            # Remove the classification head to extract latent feature representations
            model.classifier = torch.nn.Sequential(
                model.classifier[0], # Linear layer
                torch.nn.Hardswish(),
                model.classifier[2]  # Dropout
            )
            model.eval()
            _vision_model = model
            _vision_transform = weights.transforms()
            print("[Vision] Pretrained MobileNetV3 Vision model initialized successfully.")
        except Exception as e:
            print(f"[Vision] Could not load torchvision weights: {e}. Using deterministic color/texture perceptual hasher.")
            _vision_model = "fallback"
    return _vision_model

def preprocess_image(image_input: Union[str, bytes, Image.Image]) -> Optional[Image.Image]:
    """Helper to convert path, bytes, or PIL Image into RGB PIL Image."""
    try:
        if isinstance(image_input, Image.Image):
            return image_input.convert("RGB")
        elif isinstance(image_input, (bytes, bytearray)):
            return Image.open(io.BytesIO(image_input)).convert("RGB")
        elif isinstance(image_input, str):
            if os.path.exists(image_input):
                return Image.open(image_input).convert("RGB")
            # If path points to uploads relative to base
            upload_full = os.path.join(settings.BASE_DIR, image_input.lstrip("/\\"))
            if os.path.exists(upload_full):
                return Image.open(upload_full).convert("RGB")
    except Exception as e:
        print(f"[Vision] Error loading image: {e}")
    return None

def generate_image_embedding(image_input: Union[str, bytes, Image.Image]) -> Optional[List[float]]:
    """
    Generates a dense visual feature embedding using the pretrained Computer Vision model.
    Extracts deep visual features including shape, color distribution, and object attributes.
    """
    img = preprocess_image(image_input)
    if img is None:
        return None

    model = get_vision_model()
    if model != "fallback" and model is not None and _vision_transform is not None:
        try:
            tensor = _vision_transform(img).unsqueeze(0)
            with torch.no_grad():
                feats = model(tensor)
                feats = feats.flatten().numpy()
                norm = np.linalg.norm(feats)
                if norm > 0:
                    feats = feats / norm
                return feats.tolist()
        except Exception as e:
            print(f"[Vision] Error during model feature extraction: {e}")

    # Perceptual Color & Spatial Texture histogram fallback
    try:
        resized = img.resize((32, 32))
        arr = np.array(resized, dtype=np.float32) / 255.0
        # Color distribution (RGB channels) + spatial blocks
        hist_r, _ = np.histogram(arr[:, :, 0], bins=32, range=(0, 1))
        hist_g, _ = np.histogram(arr[:, :, 1], bins=32, range=(0, 1))
        hist_b, _ = np.histogram(arr[:, :, 2], bins=32, range=(0, 1))
        # Spatial thumbnail features
        spatial = arr.mean(axis=2).flatten()[:288] # 288 spatial features
        full_vec = np.concatenate([hist_r, hist_g, hist_b, spatial]) # 384 dimensions
        norm = np.linalg.norm(full_vec)
        if norm > 0:
            full_vec = full_vec / norm
        return full_vec.tolist()
    except Exception as e:
        print(f"[Vision] Perceptual fallback failed: {e}")
        return [0.0] * 384

def calculate_image_similarity(
    embedding1: Optional[Union[List[float], np.ndarray]],
    embedding2: Optional[Union[List[float], np.ndarray]]
) -> float:
    """
    Calculates cosine similarity between two visual embeddings.
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
    return max(0.0, min(1.0, (sim + 1.0) / 2.0 if sim < 0 else sim))
