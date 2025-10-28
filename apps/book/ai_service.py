import re
from textblob import TextBlob
import warnings
from typing import Optional, List

warnings.filterwarnings('ignore')

class AIService:
    def __init__(self):
        self.nlp = None
        self.generator = None
        self.generation_model_name = 'dbddv01/gpt2-french-small'
        self.fallback_model_name = 'distilgpt2'
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

    def _ensure_generator(self):
        if self.generator is not None:
            return
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
            try:
                tokenizer = AutoTokenizer.from_pretrained(self.generation_model_name)
                model = AutoModelForCausalLM.from_pretrained(self.generation_model_name)
            except Exception:
                tokenizer = AutoTokenizer.from_pretrained(self.fallback_model_name)
                model = AutoModelForCausalLM.from_pretrained(self.fallback_model_name)
            self.generator = pipeline('text-generation', model=model, tokenizer=tokenizer)
        except Exception:
            self.generator = None
    
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

    def suggest_continue(self, text: str, max_new_tokens: int = 80, num_return_sequences: int = 3, temperature: float = 0.9, top_p: float = 0.95):
        try:
            self._ensure_generator()
            if self.generator is None:
                return {'success': False, 'error': "Impossible de charger le modèle de génération (transformers)", 'suggestions': []}
            prompt = (text.strip()[-600:] if len(text) > 600 else text).strip()
            if not prompt:
                return {'success': False, 'error': 'Texte vide', 'suggestions': []}
            outputs = self.generator(
                prompt,
                max_new_tokens=max_new_tokens,
                num_return_sequences=num_return_sequences,
                do_sample=True,
                temperature=temperature,
                top_p=top_p,
                eos_token_id=None
            )
            suggestions = []
            for out in outputs:
                gen = out.get('generated_text', '')
                cont = gen[len(prompt):].strip() if gen.startswith(prompt) else gen.strip()
                suggestions.append(cont)
            return {'success': True, 'suggestions': suggestions}
        except Exception as e:
            return {'success': False, 'error': str(e), 'suggestions': []}

    def rewrite_text(self, text: str, style: str = 'simple', max_new_tokens: int = 120):
        try:
            self._ensure_generator()
            if self.generator is None:
                return {'success': False, 'error': "Impossible de charger le modèle de génération", 'rewrites': []}
            style_map = {
                'simple': 'Réécris ce texte en français plus simple et clair, en conservant le sens:',
                'formel': 'Réécris ce texte en français plus formel et professionnel:',
                'concis': 'Réécris ce texte en français de manière plus concise:',
            }
            instruction = style_map.get(style, style_map['simple'])
            prompt = f"{instruction}\n\nTexte:\n{text.strip()}\n\nRéécriture: "
            outputs = self.generator(
                prompt,
                max_new_tokens=max_new_tokens,
                num_return_sequences=3,
                do_sample=True,
                temperature=0.8,
                top_p=0.95
            )
            rewrites = []
            for out in outputs:
                gen = out.get('generated_text', '')
                after = gen.split('Réécriture:', 1)
                candidate = after[1] if len(after) > 1 else gen
                rewrites.append(candidate.strip())
            return {'success': True, 'style': style, 'rewrites': rewrites}
        except Exception as e:
            return {'success': False, 'error': str(e), 'rewrites': []}

    def suggest_titles(self, text: str, num_titles: int = 5):
        try:
            self._ensure_generator()
            if self.generator is None:
                return {'success': False, 'error': "Impossible de charger le modèle de génération", 'titles': []}
            snippet = text.strip()[:800]
            prompt = (
                "Propose des titres courts et accrocheurs en français pour le texte suivant.\n"
                "Contraintes: chaque titre entre 5 et 8 mots, pas de numérotation.\n"
                "Format: liste avec un tiret en début de ligne.\n\n"
                f"Texte:\n{snippet}\n\nExemples:\n"
                "- Les Ombres de la Cité Perdue\n"
                "- Chroniques d'un Destin Brisé\n"
                "- Secrets au Bord de la Rivière\n\n"
                "Titres:\n- "
            )
            outputs = self.generator(
                prompt,
                max_new_tokens=96,
                num_return_sequences=3,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.2
            )
            raw = "\n".join(o.get('generated_text', '') for o in outputs)
            candidates = []
            for l in raw.splitlines():
                s = l.strip()
                if not s.startswith('-'):
                    continue
                t = s.lstrip('-').strip()
                t = re.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ'\-\s]", " ", t)
                t = re.sub(r"\s+", " ", t).strip()
                words = t.split()
                if len(words) < 5 or len(words) > 8:
                    continue
                if t.endswith(('.', ',', ';', ':', '!', '?')):
                    t = t[:-1].strip()
                t = t[:1].upper() + t[1:]
                candidates.append(t)
            seen = set()
            titles = []
            for t in candidates:
                k = t.lower()
                if k in seen:
                    continue
                seen.add(k)
                titles.append(t)
                if len(titles) >= num_titles:
                    break
            if len(titles) < num_titles:
                kw = self.extract_keywords(text).get('keywords', [])
                base = [k.get('word') for k in kw][:6]
                patterns = [
                    "Chroniques de {} et {}",
                    "Les Secrets de {}",
                    "Au Cœur de {}",
                    "L'Ombre de {}",
                    "Mystère sur {}"
                ]
                i = 0
                while len(titles) < num_titles and i < len(patterns):
                    if len(base) >= 2:
                        t = patterns[i].format(base[0].capitalize(), base[1].capitalize()) if '{}' in patterns[i] and patterns[i].count('{}') == 2 else patterns[i].format(base[0].capitalize())
                        titles.append(t)
                    i += 1
            return {'success': True, 'titles': titles[:num_titles]}
        except Exception as e:
            return {'success': False, 'error': str(e), 'titles': []}


ai_service = AIService()
