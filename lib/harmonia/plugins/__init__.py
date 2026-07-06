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
    # 1. Tensor / Embedding Engine Selection (Spatial Projection)
    # =========================================================================
    embed_loaded = False
    
    # Priority 1: Heavy TensorFlow Engine
    if env_context.get("has_tf", False):
        try:
            from . import tensor_engine
            if hasattr(tensor_engine, "register"):
                tensor_engine.register(harmonia_engine)
                embed_loaded = True
                logger.info("[Plugin] Registered: sys.embed (TensorFlow Engine)")
        except ImportError as e:
            logger.warning(f"TF engine load failed despite env claim: {e}")

    # Priority 2: Lightweight TFLite Engine (Edge/Tablet fallback)
    if not embed_loaded and env_context.get("has_tflite", False):
        try:
            from . import tflite_engine
            if hasattr(tflite_engine, "register"):
                tflite_engine.register(harmonia_engine)
                embed_loaded = True
                logger.info("[Plugin] Registered: sys.embed (TFLite Engine)")
        except ImportError as e:
            logger.warning(f"TFLite engine load failed: {e}")

    # =========================================================================
    # 2. NLP / Cognitive Extraction Selection
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

