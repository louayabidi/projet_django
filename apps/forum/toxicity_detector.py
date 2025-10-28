# apps/forum/toxicity_detector.py
from transformers import pipeline
import logging

logger = logging.getLogger(__name__)

class ToxicityDetector:
    def __init__(self):
        try:
            
            self.classifier = pipeline(
                "text-classification",
                model="unitary/toxic-bert",
                tokenizer="unitary/toxic-bert",
                top_k=None  
            )
            self.is_loaded = True
            logger.info("Modèle de toxicité chargé avec succès")
        except Exception as e:
            self.is_loaded = False
            logger.error(f"Erreur lors du chargement du modèle: {e}")

    def analyze_toxicity(self, text):
        """
        Analyse la toxicité d'un texte et retourne le score maximum
        """
        if not self.is_loaded or not text.strip():
            return 0.0
        
        try:
            # Analyser le texte
            results = self.classifier(text)
            
            # Trouver le score de toxicité maximum parmi toutes les catégories
            max_toxicity = 0.0
            for category in results[0]:
                if category['score'] > max_toxicity:
                    max_toxicity = category['score']
            
            logger.info(f"Texte analysé: '{text[:50]}...' - Toxicité: {max_toxicity:.3f}")
            return max_toxicity
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse: {e}")
            return 0.0

# Instance globale
toxicity_detector = ToxicityDetector()