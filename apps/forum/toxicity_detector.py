# apps/forum/toxicity_detector.py
from transformers import pipeline
import logging

logger = logging.getLogger(__name__)

class ToxicityDetector:
    def __init__(self):
        # Don't load model at initialization
        self._classifier = None
        self.is_loaded = False
        logger.info("ToxicityDetector initialized (model will load on first use)")
    
    def _load_model(self):
        """Load model only when first needed"""
        if self._classifier is None:
            try:
                logger.info("🔄 Loading toxicity model for the first time...")
                self._classifier = pipeline(
                    "text-classification",
                    model="unitary/toxic-bert",
                    tokenizer="unitary/toxic-bert",
                    top_k=None,
                    device=-1  # Force CPU
                )
                self.is_loaded = True
                logger.info("✅ Toxicity model loaded successfully")
            except Exception as e:
                self.is_loaded = False
                logger.error(f"❌ Error loading toxicity model: {e}")
        
        return self._classifier

    def analyze_toxicity(self, text):
        """
        Analyze text toxicity (loads model on first call)
        """
        if not text or not text.strip():
            return 0.0
        
        try:
            # Load model on first use
            classifier = self._load_model()
            
            if not classifier:
                logger.warning("Model not loaded, returning safe score")
                return 0.0
            
            # Analyze text
            results = classifier(text)
            
            # Find maximum toxicity score
            max_toxicity = 0.0
            for category in results[0]:
                if category['score'] > max_toxicity:
                    max_toxicity = category['score']
            
            logger.info(f"Texte analysé: '{text[:50]}...' - Toxicité: {max_toxicity:.3f}")
            return max_toxicity
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse: {e}")
            return 0.0

# Global instance (model loads lazily)
toxicity_detector = ToxicityDetector()