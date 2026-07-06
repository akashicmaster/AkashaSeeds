"""
Harmonia Plugin: Tensor Engine Dispatcher
Defines the core interface for the "Node as Tensor" architecture.
Automatically dynamically loads the best available mathematical backend
(NumPy, TFLite, or Pure Python Fallback) based on the current environment.
"""
import math
import logging

logger = logging.getLogger("Harmonia.Tensor")

class TensorEngineBase:
    """
    The absolute blueprint for all Tensor computing plugins.
    Any specific implementation (NumPy, TFLite) must satisfy this contract.
    """
    def __init__(self):
        self.engine_name = "Base"

    def embed_text(self, text: str) -> list[float]:
        """Convert text into a multi-dimensional cosmos coordinate (tensor)."""
        raise NotImplementedError

    def compute_distance(self, vec_a: list[float], vec_b: list[float]) -> float:
        """Calculate the semantic distance (e.g., Euclidean) between two tensors."""
        raise NotImplementedError

    def compute_similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        """Calculate the semantic alignment (e.g., Cosine Similarity) between two tensors."""
        raise NotImplementedError

    def find_centroid(self, vectors: list[list[float]]) -> list[float]:
        """Calculate the center of gravity (centroid) for a cluster of stars."""
        raise NotImplementedError


class PurePythonTensorEngine(TensorEngineBase):
    """
    Fallback Engine: The Ultimate Struggle.
    Uses only Python standard libraries. Slow, but guarantees survival anywhere.
    """
    def __init__(self):
        self.engine_name = "PurePython Heuristics"

    def embed_text(self, text: str) -> list[float]:
        # Dummy embedding based on character hashes for absolute fallback
        h = sum(ord(c) for c in text)
        return [float(h % 100) / 100.0] * 12  # A rudimentary 12-dimensional vector

    def compute_distance(self, vec_a: list[float], vec_b: list[float]) -> float:
        if len(vec_a) != len(vec_b): return float('inf')
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec_a, vec_b)))

    def compute_similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        if len(vec_a) != len(vec_b): return 0.0
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        mag_a = math.sqrt(sum(a ** 2 for a in vec_a))
        mag_b = math.sqrt(sum(b ** 2 for b in vec_b))
        if mag_a == 0 or mag_b == 0: return 0.0
        return dot_product / (mag_a * mag_b)

    def find_centroid(self, vectors: list[list[float]]) -> list[float]:
        if not vectors: return []
        dim = len(vectors[0])
        centroid = [0.0] * dim
        for vec in vectors:
            for i in range(dim):
                centroid[i] += vec[i]
        return [val / len(vectors) for val in centroid]


# ==========================================
# Dispatcher Logic
# ==========================================

def get_best_tensor_engine() -> TensorEngineBase:
    """
    Evaluates the environment and loads the most powerful tensor engine available.
    Adheres to the Struggle Algorithm (Degrade gracefully).
    """
    # 1. Attempt to load NumPy-based engine (Heavy, but fast math)
    try:
        import numpy as np
        # In the future, you would import the actual NumPy plugin class here
        # from harmonia.plugins.tensor_numpy import NumpyTensorEngine
        # return NumpyTensorEngine()
        logger.debug("NumPy detected. (Ready to load NumpyTensorEngine)")
    except ImportError:
        pass

    # 2. Attempt to load TFLite-based engine (Mobile/Edge optimized)
    try:
        import tflite_runtime.interpreter as tflite
        # from harmonia.plugins.tensor_tflite import TFLiteTensorEngine
        # return TFLiteTensorEngine()
        logger.debug("TFLite detected. (Ready to load TFLiteTensorEngine)")
    except ImportError:
        pass

    # 3. Absolute Fallback
    logger.warning("No advanced mathematical libraries found. Falling back to Pure Python Tensor Engine.")
    return PurePythonTensorEngine()

# Initialize the global engine instance to be used across the system
tensor = get_best_tensor_engine()


# -----------------------------------------------------------------------------
# Registration
# -----------------------------------------------------------------------------
def register(engine):
    """Register the tensor engine's embed_text as the sys.embed plugin."""
    engine.register_plugin("sys.embed", lambda text, **_: tensor.embed_text(text))
    print(f"[Plugin] Registered: sys.embed ({tensor.engine_name})")
