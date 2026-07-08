"""
Harmonia Plugin Dynamic Loader.
Evaluates environment capabilities (surveyed by akasha.py) and selectively loads optimal engines.
Supports progressive degradation (e.g., Heavy TF -> Edge TFLite -> External API).
"""
import logging
from typing import Dict, Any

logger = logging.getLogger("Harmonia.Plugins")

def load_plugins(harmonia_engine, env_context: Dict[str, Any] = None):
    """
    Evaluates the environment and registers the optimal execution engines into Harmonia.
    
    Args:
        harmonia_engine: The core HarmoniaEngine instance.
        env_context: Dictionary containing environment capabilities surveyed at boot.
                     (e.g., {"has_tf": True, "has_tflite": True, "has_local_nlp": False})
    """
    if env_context is None:
        env_context = {}

    logger.info("[Harmonia] Initializing cognitive and motor plugins...")

    # =========================================================================
    # Tensor / Embedding — NOTE: the former tensor_engine / tflite_engine plugins
    # (`sys.embed` / `sys.tflite.embed`) were removed. They were never registered
    # (this loader had no caller) and their "embeddings" were hash-random noise, not
    # inference. The real, self-owned embedding stack lives in lib/akasha/tensor.py +
    # semantic_learn.py, and image inference in lib/akasha/vision.py (LiteRT). Nothing
    # here should re-add a stub embedding path.
    # =========================================================================

    # =========================================================================
    # NLP / Cognitive Extraction Selection
    # =========================================================================
    # Always attempt to load the local NLP plugin. MultiLocaleNLP uses
    # Symbiosis.ensure() to auto-install SpaCy when absent, so this works on
    # any standard Linux/Codespaces environment without pre-configuration.
    try:
        from . import nlp
        if hasattr(nlp, "register"):
            nlp.register(harmonia_engine)
            logger.info("[Plugin] Registered: nlp.extract (Multi-locale SpaCy)")
    except ImportError as e:
        logger.warning(f"NLP plugin failed to load: {e}")

