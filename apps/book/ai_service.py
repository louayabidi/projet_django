import re
from textblob import TextBlob
import warnings

warnings.filterwarnings('ignore')

class AIService:
    def __init__(self):
        self.nlp = None
        try:
            import spacy
            try:
                self.nlp = spacy.load('en_core_web_sm')
            except OSError:
                import subprocess
                import sys
                subprocess.check_call([sys.executable, '-m', 'spacy', 'download', 'en_core_web_sm'])
                self.nlp = spacy.load('en_core_web_sm')
        except Exception:
            self.nlp = None
    
    def correct_grammar(self, text):
        try:
            corrections = []
            
            common_errors = {
                'ca ': 'ça ',
                'cest ': "c'est ",
                'detre': "d'être",
                'lorsque ': 'lorsque ',
                'quil': "qu'il",
                'quelle': "qu'elle",
                'jai': "j'ai",
                'jais': "j'ai",
                'trop de  ': 'trop de ',
                '  ': ' '
            }
            
            corrected_text = text
            for error, correction in common_errors.items():
                if error in text.lower():
                    corrected_text = corrected_text.replace(error, correction)
                    corrected_text = corrected_text.replace(error.upper(), correction.upper())
            
            if corrected_text != text:
                corrections.append({
                    'original': text,
                    'corrected': corrected_text,
                    'type': 'grammar',
                    'note': 'Corrections mineures détectées'
                })
            else:
                corrections.append({
                    'original': text,
                    'corrected': text,
                    'type': 'grammar',
                    'note': 'Aucune erreur évidente détectée'
                })
            
            return {
                'success': True,
                'corrections': corrections,
                'corrected_text': corrected_text,
                'count': len(corrections)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'corrections': []
            }
    
    def generate_synopsis(self, text, max_length=150, min_length=50):
        try:
            if len(text.split()) < 50:
                return {
                    'success': False,
                    'error': 'Le texte doit contenir au moins 50 mots pour générer un synopsis',
                    'synopsis': None
                }
            
            sentences = text.split('.')
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) < 2:
                synopsis = text[:200] + '...'
            else:
                num_sentences = max(1, len(sentences) // 3)
                synopsis = '. '.join(sentences[:num_sentences]) + '.'
            
            return {
                'success': True,
                'synopsis': synopsis,
                'original_length': len(text.split()),
                'summary_length': len(synopsis.split())
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'synopsis': None
            }
    
    def analyze_sentiment(self, text):
        try:
            text_lower = text.lower()
            
            positive_words = ['amour', 'love', 'bonheur', 'happy', 'joy', 'joie', 'magnifique', 'wonderful', 'excellent', 'merveilleux', 'beau', 'beautiful', 'adorable', 'fantastique', 'super', 'great', 'awesome', 'parfait', 'perfect']
            negative_words = ['triste', 'sad', 'douleur', 'pain', 'mort', 'death', 'peur', 'fear', 'horreur', 'horror', 'larme', 'tear', 'souffrance', 'suffering', 'mal', 'bad', 'terrible', 'awful', 'horrible', 'mauvais', 'perte', 'loss', 'tumulte', 'chaos']
            
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            if positive_count > negative_count:
                sentiment = 'Positif 😊'
                raw = 'POSITIVE'
                confidence = min(100, (positive_count / max(1, positive_count + negative_count)) * 100)
            elif negative_count > positive_count:
                sentiment = 'Négatif 😞'
                raw = 'NEGATIVE'
                confidence = min(100, (negative_count / max(1, positive_count + negative_count)) * 100)
            else:
                if polarity > 0.1:
                    sentiment = 'Positif 😊'
                    raw = 'POSITIVE'
                    confidence = abs(polarity) * 100
                elif polarity < -0.1:
                    sentiment = 'Négatif 😞'
                    raw = 'NEGATIVE'
                    confidence = abs(polarity) * 100
                else:
                    sentiment = 'Neutre 😐'
                    raw = 'NEUTRAL'
                    confidence = 50.0
            
            return {
                'success': True,
                'sentiment': sentiment,
                'confidence': round(confidence, 2),
                'raw_sentiment': raw
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'sentiment': None
            }
    
    def extract_keywords(self, text):
        try:
            blob = TextBlob(text)
            words = blob.words
            
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
            
            word_freq = {}
            for word in words:
                word_lower = word.lower()
                if len(word_lower) > 3 and word_lower not in stop_words:
                    word_freq[word_lower] = word_freq.get(word_lower, 0) + 1
            
            top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            keywords = [{'word': word, 'frequency': freq} for word, freq in top_keywords]
            
            return {
                'success': True,
                'keywords': keywords,
                'count': len(keywords)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'keywords': []
            }
    
    def detect_genre(self, text):
        try:
            text_lower = text.lower()
            
            genre_keywords = {
                'Romance': ['amour', 'love', 'coeur', 'heart', 'passion', 'couple', 'mariage', 'wedding', 'embrasser', 'kiss', 'tendresse', 'affection'],
                'Science-fiction': ['futur', 'future', 'robot', 'alien', 'space', 'espace', 'technologie', 'technology', 'planète', 'galaxy', 'vaisseau'],
                'Fantaisie': ['magie', 'magic', 'dragon', 'wizard', 'enchanted', 'sort', 'spell', 'magique', 'enchantement', 'créature'],
                'Thriller': ['meurtre', 'murder', 'crime', 'danger', 'suspense', 'peur', 'fear', 'mystère', 'mystery', 'secret'],
                'Drame': ['larmes', 'tears', 'souffrance', 'suffering', 'mort', 'death', 'tragédie', 'tragedy', 'douleur', 'pain', 'tumulte', 'chaos', 'perte', 'loss', 'triste', 'sad'],
                'Comédie': ['rire', 'laugh', 'humour', 'funny', 'drôle', 'comique', 'amusant', 'blague', 'joke', 'hilare'],
                'Horreur': ['peur', 'fear', 'monstre', 'monster', 'zombie', 'fantôme', 'ghost', 'terreur', 'terror', 'horrifique', 'macabre'],
                'Aventure': ['voyage', 'journey', 'quête', 'quest', 'exploration', 'danger', 'héros', 'hero', 'combat', 'battle', 'expédition']
            }
            
            genre_scores = {}
            for genre, keywords in genre_keywords.items():
                score = sum(1 for kw in keywords if kw in text_lower)
                genre_scores[genre] = score
            
            max_score = max(genre_scores.values()) if genre_scores else 1
            sorted_genres = sorted(genre_scores.items(), key=lambda x: x[1], reverse=True)
            
            detected_genres = []
            for genre, score in sorted_genres[:3]:
                if score > 0:
                    confidence = round((score / max(1, max_score)) * 100, 2)
                    detected_genres.append({'genre': genre, 'confidence': confidence})
                else:
                    detected_genres.append({'genre': genre, 'confidence': 0.0})
            
            return {
                'success': True,
                'genres': detected_genres,
                'primary_genre': detected_genres[0]['genre'] if detected_genres and detected_genres[0]['confidence'] > 0 else 'Général'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'genres': []
            }
    
    def analyze_readability(self, text):
        try:
            blob = TextBlob(text)
            
            sentences = len(blob.sentences)
            words = len(blob.words)
            characters = len(text)
            
            avg_word_length = characters / words if words > 0 else 0
            avg_sentence_length = words / sentences if sentences > 0 else 0
            
            if avg_sentence_length < 15:
                readability = "Très facile à lire"
                level = "Enfant"
            elif avg_sentence_length < 20:
                readability = "Facile à lire"
                level = "Adolescent"
            elif avg_sentence_length < 25:
                readability = "Moyen"
                level = "Adulte"
            else:
                readability = "Difficile à lire"
                level = "Avancé"
            
            return {
                'success': True,
                'readability': readability,
                'level': level,
                'avg_sentence_length': round(avg_word_length, 2),
                'avg_word_length': round(avg_sentence_length, 2),
                'total_words': words,
                'total_sentences': sentences
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def full_analysis(self, text):
        return {
            'grammar': self.correct_grammar(text),
            'synopsis': self.generate_synopsis(text),
            'sentiment': self.analyze_sentiment(text),
            'keywords': self.extract_keywords(text),
            'genre': self.detect_genre(text),
            'readability': self.analyze_readability(text)
        }


ai_service = AIService()
