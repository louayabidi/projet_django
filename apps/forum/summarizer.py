# apps/forum/summarizer.py
from transformers import pipeline
import logging
import re

logger = logging.getLogger(__name__)

class DiscussionSummarizer:
    def __init__(self):
        try:
            # Modèle français pour le résumé
            self.summarizer = pipeline(
                "summarization",
                model="moussaKam/barthez-orangesum-abstract"
            )
            self.is_loaded = True
            logger.info("✅ Modèle de résumé chargé avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur chargement modèle: {e}")
            self.is_loaded = False

    def should_summarize(self, text):
        """Détermine si le texte est assez long pour être résumé"""
        if not text:
            return False
        return len(text.split()) > 80

    def summarize_text(self, text, max_length=150, min_length=50):
        """
        Résume un texte en français
        """
        if not self.is_loaded:
            return self._fallback_summary(text)
        
        # Nettoyer le texte
        cleaned_text = self._clean_text(text)
        
        # Vérifier si le texte est assez long pour être résumé
        word_count = len(cleaned_text.split())
        if word_count < 80:
            return self._get_short_text_summary(cleaned_text)
        
        try:
            # Appliquer le résumé
            summary = self.summarizer(
                cleaned_text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
                truncation=True
            )
            
            result = summary[0]['summary_text'].strip()
            logger.info(f"📝 Résumé généré: {len(result)} caractères")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du résumé: {e}")
            return self._fallback_summary(text)

    def _clean_text(self, text):
        """Nettoie le texte pour le résumé"""
        # Supprimer les URLs
        text = re.sub(r'http\S+', '', text)
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        # Limiter la longueur pour éviter les erreurs
        return text[:2000].strip()

    def _fallback_summary(self, text):
        """Résumé de fallback si le modèle échoue"""
        sentences = text.split('.')
        if len(sentences) > 2:
            return '. '.join(sentences[:2]) + '.'
        return text[:150] + '...' if len(text) > 150 else text

    def _get_short_text_summary(self, text):
        """Gestion des textes courts"""
        if len(text) <= 150:
            return text
        return text[:147] + '...'

# Instance globale
discussion_summarizer = DiscussionSummarizer()