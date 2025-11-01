# apps/forum/summarizer.py
from transformers import pipeline
import logging
import re

logger = logging.getLogger(__name__)

class DiscussionSummarizer:
    def __init__(self):
        # Don't load model at initialization
        self._summarizer = None
        self.is_loaded = False
        logger.info("DiscussionSummarizer initialized (model will load on first use)")
    
    def _load_model(self):
        """Load model only when first needed"""
        if self._summarizer is None:
            try:
                logger.info("🔄 Loading summarizer model for the first time...")
                self._summarizer = pipeline(
                    "summarization",
                    model="moussaKam/barthez-orangesum-abstract",
                    device=-1  # Force CPU
                )
                self.is_loaded = True
                logger.info("✅ Summarizer model loaded successfully")
            except Exception as e:
                logger.error(f"❌ Error loading summarizer: {e}")
                self.is_loaded = False
        
        return self._summarizer

    def should_summarize(self, text):
        """Determine if text is long enough to summarize"""
        if not text:
            return False
        return len(text.split()) > 80

    def summarize_text(self, text, max_length=150, min_length=50):
        """
        Summarize text in French (loads model on first call)
        """
        if not text:
            return ""
        
        # Clean text
        cleaned_text = self._clean_text(text)
        
        # Check if text is long enough
        word_count = len(cleaned_text.split())
        if word_count < 80:
            return self._get_short_text_summary(cleaned_text)
        
        try:
            # Load model on first use
            summarizer = self._load_model()
            
            if not summarizer:
                return self._fallback_summary(text)
            
            # Apply summarization
            summary = summarizer(
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
        """Clean text for summarization"""
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Limit length to avoid errors
        return text[:2000].strip()

    def _fallback_summary(self, text):
        """Fallback summary if model fails"""
        sentences = text.split('.')
        if len(sentences) > 2:
            return '. '.join(sentences[:2]) + '.'
        return text[:150] + '...' if len(text) > 150 else text

    def _get_short_text_summary(self, text):
        """Handle short texts"""
        if len(text) <= 150:
            return text
        return text[:147] + '...'

# Global instance (model loads lazily)
discussion_summarizer = DiscussionSummarizer()