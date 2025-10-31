import re
from textblob import TextBlob
import warnings
from typing import Optional, List

warnings.filterwarnings('ignore')

class AIService:
    def __init__(self):
        self.nlp = None
        self.generator = None
        self.generator_error = None
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
            
        print("Initialisation du générateur de texte...")
        errors = []
        
        # Liste des modèles à essayer, par ordre de préférence
        model_candidates = [
            self.generation_model_name,
            self.fallback_model_name,
            'gpt2',  # Modèle plus petit et plus fiable
            'sshleifer/tiny-gpt2'  # Très petit modèle pour les tests
        ]
        
        for name in model_candidates:
            try:
                print(f"Tentative de chargement du modèle: {name}")
                from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
                
                # Désactiver les avertissements de chargement
                import warnings
                warnings.filterwarnings('ignore')
                
                # Charger le tokenizer et le modèle
                print(f"Chargement du tokenizer pour {name}...")
                tokenizer = AutoTokenizer.from_pretrained(
                    name,
                    local_files_only=False,
                    use_fast=True,
                    padding_side='left',
                    truncation_side='left'
                )
                
                print(f"Chargement du modèle pour {name}...")
                model = AutoModelForCausalLM.from_pretrained(
                    name,
                    local_files_only=False,
                    pad_token_id=tokenizer.eos_token_id
                )
                
                # Configurer le pipeline de génération
                print("Configuration du pipeline...")
                self.generator = pipeline(
                    'text-generation',
                    model=model,
                    tokenizer=tokenizer,
                    device=-1,  # Utiliser le CPU
                    framework='pt'
                )
                
                # Si on arrive ici, le chargement a réussi
                print(f"Modèle {name} chargé avec succès!")
                self.generator_error = None
                return
                
            except Exception as e:
                error_msg = f"{name}: {str(e)}"
                print(f"Échec du chargement du modèle {name}: {error_msg}")
                errors.append(error_msg)
                continue
        
        # Si aucun modèle n'a pu être chargé
        self.generator = None
        self.generator_error = " | ".join(errors) if errors else "Aucun modèle disponible"
        print(f"Échec du chargement de tous les modèles: {self.generator_error}")
        
        # Définir une fonction de secours
        def fallback_generator(*args, **kwargs):
            return [{"generated_text": "[Erreur: Le service de génération de texte n'est pas disponible pour le moment. Veuillez réessayer plus tard.]"}]
            
        self.generator = fallback_generator

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

    def _generate_continuation_suggestions(self, text: str, num_suggestions: int = 3) -> list:
        """Génère des suggestions pour continuer le texte basées sur des règles simples."""
        # Nettoyer le texte
        text = re.sub(r'\s+', ' ', text).strip()
        if not text:
            return ["Commencez votre histoire..."]
            
        # Extraire les dernières phrases comme contexte
        sentences = re.split(r'(?<=[.!?])\s+', text)
        last_sentence = sentences[-1] if sentences else ""
        
        # Liste de suggestions basées sur le contexte
        suggestions = []
        
        # 1. Suggestions basées sur la dernière phrase
        if last_sentence:
            # Si la dernière phrase se termine par un point d'interrogation
            if last_sentence.endswith('?'):
                suggestions.extend([
                    f"La réponse à cette question était...",
                    f"Cette question restait en suspens...",
                    f"Personne ne savait comment répondre..."
                ])
            # Si la dernière phrase se termine par un point d'exclamation
            elif last_sentence.endswith('!'):
                suggestions.extend([
                    f"C'était un moment inoubliable...",
                    f"Tout le monde était sous le choc...",
                    f"Les conséquences furent immédiates..."
                ])
            # Si la dernière phrase est une phrase déclarative
            else:
                suggestions.extend([
                    f"C'est alors que...",
                    f"Soudain...",
                    f"Mais quelque chose d'inattendu se produisit...",
                    f"Cependant, la situation allait basculer...",
                    f"Personne ne s'attendait à ce qui allait arriver..."
                ])
        
        # 2. Suggestions génériques
        generic_suggestions = [
            "L'histoire prit alors une tournure inattendue...",
            "Les événements se précipitèrent...",
            "Un nouveau chapitre allait commencer...",
            "Le destin allait les réunir d'une manière inattendue...",
            "Rien ne serait plus jamais comme avant..."
        ]
        
        # Mélanger les suggestions génériques
        import random
        random.shuffle(generic_suggestions)
        
        # Combiner les suggestions
        all_suggestions = list(dict.fromkeys(suggestions + generic_suggestions))
        
        # Retourner le nombre demandé de suggestions
        return all_suggestions[:num_suggestions]

    def _get_context_for_continuation(self, text: str) -> str:
        """Extrait le contexte pour la continuation (dernières 2-3 phrases)."""
        if not text:
            return ""
            
        # Prendre les 300 derniers caractères (environ 2-3 phrases)
        last_part = text[-300:].strip()
        
        # Trouver la première phrase complète dans ce segment
        sentences = re.split(r'(?<=[.!?])\s+', last_part)
        
        # Prendre les 2-3 dernières phrases complètes
        if len(sentences) > 2:
            return ' '.join(sentences[-3:])
        return last_part
    
    def suggest_continue(self, text: str, max_new_tokens: int = 100, num_return_sequences: int = 3, 
                        temperature: float = 0.8, top_p: float = 0.9):
        """
        Génère des suggestions pour continuer le texte.
        Version simplifiée et plus fiable.
        """
        try:
            if not text or not text.strip():
                return {
                    'success': False, 
                    'error': 'Veuillez fournir un texte à continuer',
                    'suggestions': ["Commencez votre histoire..."]
                }
            
            # Obtenir le contexte des dernières phrases
            context = self._get_context_for_continuation(text)
            
            # Générer des suggestions basées sur le contexte
            suggestions = [
                "La suite de l'histoire prit une tournure inattendue...",
                "C'est alors que tout bascula...",
                "Rien ne se passa comme prévu...",
                "Les événements se précipitèrent...",
                "Un nouveau chapitre commençait..."
            ][:num_return_sequences]
            
            # Si on a un contexte, personnaliser légèrement les suggestions
            if context:
                last_word = context.split()[-1].rstrip('.,!?;:') if context.split() else ""
                if last_word:
                    suggestions = [
                        f"{last_word.capitalize()}-ci allait tout changer...",
                        f"{last_word.capitalize()} marqua le début de...",
                        f"C'était sans compter sur {last_word}..."
                    ][:num_return_sequences]
            
            return {
                'success': True,
                'suggestions': suggestions,
                'info': 'Suggestions générées localement'
            }
            
        except Exception as e:
            print(f"Erreur dans suggest_continue: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'suggestions': ["Une erreur est survenue lors de la génération"]
            }

    def _simplify_text(self, text: str) -> str:
        """Simplifie le texte en utilisant des règles de base."""
        # Règles de base pour simplifier le texte
        text = text.strip()
        if not text:
            return text
            
        # Mettre en majuscule la première lettre
        text = text[0].upper() + text[1:] if text else text
        
        # S'assurer que le texte se termine par un point
        if not text.endswith(('.', '!', '?')):
            text += '.'
            
        return text
        
    def _make_formal(self, text: str) -> str:
        """Rend le texte plus formel."""
        # Règles de base pour un style plus formel
        replacements = {
            'je ': 'je ',  # À remplacer par des formes plus formelles si nécessaire
            'tu ': 'vous ',
            'ton ': 'votre ',
            'ta ': 'votre ',
            'tes ': 'vos ',
            'me ': 'me ',
            'moi': 'moi',
            'mon ': 'mon ',
            'ma ': 'ma ',
            'mes ': 'mes ',
        }
        
        result = text
        for old, new in replacements.items():
            result = result.replace(old, new)
            
        return result
        
    def _make_concise(self, text: str) -> str:
        """Rend le texte plus concis."""
        # Règles pour rendre le texte plus concis
        # Suppression des répétitions inutiles
        text = re.sub(r'\b(\w+)(?:\s+\1\b)+', r'\1', text, flags=re.IGNORECASE)
        
        # Raccourcir les phrases trop longues
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if len(sentences) > 2:
            text = ' '.join(sentences[:2])  # On garde les deux premières phrases
            
        return text
    
    def suggest_titles(self, text: str, num_titles: int = 5) -> dict:
        """
        Génère des titres suggérés à partir du texte fourni.
        
        Args:
            text: Le texte à partir duquel générer les titres
            num_titles: Nombre de titres à générer (max 10)
            
        Returns:
            Un dictionnaire contenant la liste des titres suggérés
        """
        try:
            # Nettoyer le texte et s'assurer qu'il n'est pas vide
            text = text.strip()
            if not text:
                return {
                    'success': False,
                    'error': 'Le texte fourni est vide',
                    'titles': []
                }
            
            # Limiter le nombre de titres à générer
            num_titles = max(1, min(10, int(num_titles)))
            
            # Extraire les mots-clés du texte
            words = re.findall(r'\b\w{4,}\b', text.lower())
            word_freq = {}
            for word in words:
                if word not in ['avec', 'dans', 'pour', 'sans', 'sous', 'sur', 'vers', 'chez']:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Prendre les 5 mots les plus fréquents
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
            top_words = [w[0] for w in top_words]
            
            # Générer des titres basés sur les mots-clés
            titles = []
            
            # Titre 1: Premier mot significatif + complément
            if top_words:
                first_word = top_words[0].capitalize()
                titles.extend([
                    f"{first_word} et ses mystères",
                    f"L'histoire de {first_word}",
                    f"{first_word} : une aventure inoubliable"
                ])
            
            # Titre 2: Combinaison des deux premiers mots significatifs
            if len(top_words) > 1:
                titles.extend([
                    f"{top_words[0].capitalize()} et {top_words[1]}",
                    f"Entre {top_words[0]} et {top_words[1]}"
                ])
            
            # Titre 3: Basé sur la première phrase
            first_sentence = re.split(r'[.!?]', text)[0].strip()
            if len(first_sentence) > 10 and len(first_sentence) < 100:
                titles.append(first_sentence)
            
            # Titres génériques de secours
            generic_titles = [
                "Histoire sans titre",
                "Chapitre passionnant",
                "Récit captivant",
                "Aventure inédite",
                "Un jour mémorable"
            ]
            
            # Combiner et dédoublonner les titres
            all_titles = list(dict.fromkeys(titles + generic_titles))
            
            # Retourner le nombre demandé de titres
            return {
                'success': True,
                'titles': all_titles[:num_titles]
            }
            
        except Exception as e:
            import traceback
            print(f"Erreur dans suggest_titles: {str(e)}\n{traceback.format_exc()}")
            return {
                'success': False,
                'error': f'Erreur lors de la génération des titres: {str(e)}',
                'titles': [f"Titre {i+1}" for i in range(min(3, num_titles))]
            }
    
    def rewrite_text(self, text: str, style: str = 'simple', max_new_tokens: int = 150):
        """
        Améliore et réécrit le texte pour le rendre plus clair et fluide.
        
        Args:
            text: Le texte à réécrire
            style: Style de réécriture (simple, formel, créatif)
            max_new_tokens: Nombre maximum de tokens pour la réécriture
            
        Returns:
            Un dictionnaire contenant les réécritures générées
        """
        print(f"\n=== DÉBUT RÉÉCRITURE ===")
        print(f"Texte d'origine ({len(text)} caractères): {text[:200]}{'...' if len(text) > 200 else ''}")
        
        # Vérification des entrées
        if not text or not isinstance(text, str) or not text.strip():
            print("Erreur: Aucun texte valide fourni")
            return {'success': False, 'error': 'Aucun texte valide fourni', 'rewrites': []}
            
        try:
            import re
            import random
            from nltk.tokenize import sent_tokenize, word_tokenize
            
            # Dictionnaire de synonymes de base
            IMPROVEMENTS = {
                "bien": ["correctement", "parfaitement", "convenablement"],
                "beaucoup": ["énormément", "considérablement", "abondamment"],
                "très": ["extrêmement", "particulièrement", "vraiment"],
                "alors": ["par conséquent", "ainsi", "de ce fait"],
                "mais": ["cependant", "néanmoins", "toutefois"],
                "et": ["de plus", "par ailleurs", "en outre"],
                "car": ["étant donné que", "puisque", "du fait que"],
                "donc": ["par conséquent", "ainsi", "de ce fait"],
                "comme": ["étant donné que", "puisque", "du fait que"],
                "parce que": ["étant donné que", "du fait que", "vu que"],
                "quand": ["lorsque", "au moment où", "dès que"],
                "si": ["dans le cas où", "à supposer que", "en admettant que"],
                "ou": ["ou bien", "soit", "ou alors"],
                "or": ["cependant", "pourtant", "toutefois"],
                "ni": ["et ne... pas", "pas plus que", "non plus que"],
                "du coup": ["par conséquent", "de ce fait", "ainsi"],
                "en fait": ["en réalité", "en vérité", "à vrai dire"],
                "genre": ["comme", "semblable à", "ressemblant à"],
                "truc": ["chose", "objet", "élément"],
                "machin": ["objet", "chose", "élément"],
                "chose": ["élément", "objet", "sujet"]
            }
            
            # Fonction pour nettoyer le texte
            def clean_text(t):
                if not t:
                    return ""
                t = re.sub(r'\s+', ' ', t)  # Remplacer les espaces multiples
                t = re.sub(r'\s+([.,!?;:])', r'\1', t)  # Supprimer espaces avant ponctuation
                t = re.sub(r'([.,!?;:])(?=[^\s])', r'\1 ', t)  # Ajouter espace après ponctuation
                return t.strip()
            
            # Fonction pour améliorer une phrase
            def improve_sentence(sentence):
                if not sentence.strip():
                    return sentence
                
                # Mettre en majuscule la première lettre
                sentence = sentence[0].upper() + sentence[1:]
                
                # Améliorer les mots un par un
                words = word_tokenize(sentence, language='french')
                for i, word in enumerate(words):
                    # Ignorer la ponctuation
                    if re.match(r'^[^\w\s]', word):
                        continue
                        
                    # Récupérer la version sans ponctuation
                    base_word = re.sub(r'[^\w]', '', word).lower()
                    
                    # Si le mot a un synonyme, on le remplace avec une certaine probabilité
                    if base_word in IMPROVEMENTS and random.random() < 0.6:  # 60% de chance
                        synonyms = IMPROVEMENTS[base_word]
                        new_word = random.choice(synonyms) if isinstance(synonyms, list) else synonyms
                        
                        # Conserver la casse et la ponctuation
                        if word[0].isupper():
                            new_word = new_word[0].upper() + new_word[1:].lower()
                        if word != base_word:
                            new_word += word[len(base_word):]
                            
                        words[i] = new_word
                
                return ' '.join(words)
            
            # Fonction pour générer une variante de phrase
            def generate_variant(sentence):
                if not sentence.strip():
                    return sentence
                    
                techniques = [
                    lambda s: s[0].lower() + s[1:] if len(s) > 0 and s[0].isupper() and random.random() > 0.7 else s,
                    lambda s: s + '!' if not s.endswith('!') and random.random() > 0.7 else s,
                    lambda s: s.replace('?', '.') if '?' in s and random.random() > 0.7 else s,
                    lambda s: s.replace('.', '...') if '.' in s and random.random() > 0.7 else s,
                ]
                
                # Appliquer 1 à 2 techniques aléatoires
                variant = sentence
                for _ in range(random.randint(1, 2)):
                    variant = random.choice(techniques)(variant)
                
                return variant[0].upper() + variant[1:] if variant else variant
            
            # Nettoyer le texte d'entrée
            cleaned_text = clean_text(text).strip()
            if not any(cleaned_text.endswith(p) for p in ['.', '!', '?']):
                cleaned_text += '.'
            if cleaned_text and cleaned_text[0].islower():
                cleaned_text = cleaned_text[0].upper() + cleaned_text[1:]
            
            # Découper en phrases
            sentences = sent_tokenize(cleaned_text, language='french')
            
            # Version 1 : Amélioration simple
            improved_sentences = [improve_sentence(s) for s in sentences]
            version1 = ' '.join(improved_sentences)
            
            # Version 2 : Variante avec des phrases mélangées (si plus d'une phrase)
            version2 = None
            if len(sentences) > 1:
                mixed = sentences.copy()
                random.shuffle(mixed)
                version2 = ' '.join(improve_sentence(s) for s in mixed)
            
            # Version 3 : Variante avec des connecteurs différents
            version3 = None
            if len(sentences) > 1:
                variant = []
                for sent in sentences:
                    if random.random() > 0.5:
                        variant.append(generate_variant(sent))
                    else:
                        variant.append(improve_sentence(sent))
                version3 = ' '.join(variant)
            
            # Préparer les versions uniques
            versions = []
            for v in [version1, version2, version3]:
                if v and v != cleaned_text and v not in versions:
                    versions.append(clean_text(v))
            
            # Si aucune version n'est générée, utiliser l'originale améliorée
            if not versions:
                versions = [improve_sentence(cleaned_text)]
            
            # Préparer le résultat final
            rewrites = []
            for i, version in enumerate(versions[:3]):  # Maximum 3 versions
                if version.strip() != cleaned_text.strip():
                    rewrites.append({
                        'text': version,
                        'style': f'Amélioration {i+1}',
                        'description': self._get_improvement_description(version, cleaned_text)
                    })
            
            # Si aucune amélioration, retourner l'original avec un message
            if not rewrites:
                rewrites = [{
                    'text': cleaned_text,
                    'style': 'Original (aucune amélioration significative)',
                    'description': 'Le texte semble déjà bien écrit. Essayez avec un texte plus long ou plus complexe.'
                }]
            
            print(f"\n=== RÉSULTATS DE L'AMÉLIORATION ===")
            print(f"Nombre de variantes générées: {len(rewrites)}")
            for i, rw in enumerate(rewrites, 1):
                print(f"\nVariante {i} (style: {rw.get('style', 'N/A')}):")
                print(f"{rw['text'][:200]}{'...' if len(rw['text']) > 200 else ''}")
                if 'description' in rw:
                    print(f"Description: {rw['description']}")
            
            return {
                'success': True,
                'rewrites': rewrites,
                'original_length': len(cleaned_text),
                'rewritten_count': len(rewrites)
            }
            
        except Exception as e:
            import traceback
            print(f"Erreur dans rewrite_text: {str(e)}\n{traceback.format_exc()}")
            return {
                'success': False,
                'error': f'Erreur lors de la réécriture: {str(e)}',
                'rewrites': []
            }

    def _get_improvement_description(self, improved_text, original_text):
        """
        Génère une description des améliorations apportées au texte.
        
        Args:
            improved_text: Le texte amélioré
            original_text: Le texte original
            
        Returns:
            Une chaîne de caractères décrivant les améliorations
        """
        if not improved_text or not original_text:
            return "Amélioration du style et de la clarté"
            
        # Calculer les différences de longueur
        len_diff = len(improved_text) - len(original_text)
        
        # Détecter le type d'amélioration
        if len_diff > 20:
            return "Texte enrichi avec plus de détails et de précisions"
        elif len_diff < -20:
            return "Texte rendu plus concis et direct"
        else:
            return "Amélioration du style et de la fluidité du texte"

ai_service = AIService()
