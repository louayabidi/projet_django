import re
import random
from nltk.tokenize import sent_tokenize, word_tokenize

class AIService:
    def __init__(self):
        # Dictionnaire de synonymes et d'améliorations
        self.IMPROVEMENTS = {
            # Formes contractées
            "j'ai": "j'ai",
            "j'suis": "je suis",
            "t'as": "tu as",
            "c'est": "c'est",
            "j'veux": "je veux",
            "j'peux": "je peux",
            "j'sais": "je sais",
            "y'a": "il y a",
            "faut": "il faut",
            
            # Mots courants et leurs améliorations
            "bien": ["correctement", "parfaitement", "convenablement"],
            "beaucoup": ["énormément", "considérablement", "substantiellement"],
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
            
            # Expressions à éviter
            "du coup": ["par conséquent", "de ce fait", "ainsi"],
            "en fait": ["en réalité", "en vérité", "à vrai dire"],
            "genre": ["comme", "semblable à", "ressemblant à"],
            "truc": ["chose", "objet", "élément"],
            "machin": ["objet", "chose", "élément"],
            "chose": ["élément", "objet", "sujet"],
            "faire": ["effectuer", "réaliser", "accomplir"],
            "dire": ["affirmer", "déclarer", "préciser"],
            "voir": ["constater", "observer", "remarquer"],
            "penser": ["considérer", "estimer", "juger"],
            "vouloir": ["souhaiter", "désirer", "aspirer à"],
            "pouvoir": ["être en mesure de", "avoir la possibilité de", "être capable de"],
            "devoir": ["être tenu de", "avoir l'obligation de", "être dans l'obligation de"],
            "falloir": ["il est nécessaire de", "il convient de", "il importe de"],
            "aller": ["se rendre", "se diriger vers", "se déplacer vers"],
            "venir": ["arriver", "se présenter", "se rendre"],
            "prendre": ["saisir", "attraper", "s'emparer de"],
            "mettre": ["placer", "déposer", "positionner"],
            "donner": ["offrir", "fournir", "procurer"],
            "savoir": ["connaître", "maîtriser", "être informé de"],
            "comprendre": ["saisir", "appréhender", "discerner"],
            "chercher": ["rechercher", "explorer", "examiner"],
            "trouver": ["découvrir", "repérer", "dénicher"],
            "parler": ["s'exprimer", "discourir", "s'entretenir"],
            "demander": ["solliciter", "questionner", "interroger"],
            "répondre": ["répliquer", "rétorquer", "réagir"],
            "essayer": ["tenter", "entreprendre", "s'efforcer de"],
            "commencer": ["débuter", "entamer", "amorcer"],
            "continuer": ["poursuivre", "persévérer", "maintenir"],
            "arrêter": ["cesser", "interrompre", "mettre fin à"],
            "changer": ["modifier", "transformer", "faire évoluer"],
            "utiliser": ["exploiter", "employer", "se servir de"],
            "montrer": ["démontrer", "exposer", "révéler"],
            "cacher": ["dissimuler", "masquer", "occulter"],
            "aimer": ["apprécier", "adorer", "préférer"],
            "détester": ["exécrer", "avoir en horreur", "ne pas supporter"],
            "croire": ["penser", "estimer", "considérer"],
            "oublier": ["omettre", "négliger", "faire abstraction de"],
            "se souvenir": ["se rappeler", "se remémorer", "se souvenir de"],
            "réussir": ["aboutir", "parvenir à", "arriver à ses fins"],
            "échouer": ["échouer dans", "ne pas aboutir", "faire un échec"],
            "aider": ["assister", "soutenir", "prêter main-forte à"],
            "empêcher": ["entraver", "faire obstacle à", "mettre un frein à"],
            "permettre": ["autoriser", "donner la possibilité de", "rendre possible"],
            "interdire": ["prohiber", "défendre", "mettre à l'index"]
        }

    def clean_text(self, text):
        """Nettoie le texte en supprimant les espaces superflus et en normalisant la ponctuation."""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)  # Remplacer les espaces multiples par un seul
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)  # Supprimer les espaces avant la ponctuation
        text = re.sub(r'([.,!?;:])(?=[^\s])', r'\1 ', text)  # Ajouter un espace après la ponctuation
        return text.strip()

    def get_synonym(self, word, probability=0.6):
        """Retourne un synonyme amélioré avec une certaine probabilité."""
        if not word or random.random() > probability:
            return word
            
        # Extraire la ponctuation finale
        base_word = re.sub(r'[^\w]', '', word).lower()
        if not base_word or base_word not in self.IMPROVEMENTS:
            return word
            
        # Obtenir un synonyme aléatoire
        synonyms = self.IMPROVEMENTS[base_word]
        if isinstance(synonyms, list):
            synonym = random.choice(synonyms)
        else:
            synonym = synonyms
            
        if not synonym:
            return word
            
        # Conserver la casse d'origine
        if word[0].isupper():
            synonym = synonym[0].upper() + synonym[1:].lower()
            
        # Conserver la ponctuation d'origine
        if word != base_word:
            suffix = word[len(base_word):]
            synonym += suffix
            
        return synonym

    def improve_sentence(self, sentence):
        """Améliore une phrase en remplaçant certains mots par des synonymes."""
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
                
            # Remplacer le mot par un synonyme avec une certaine probabilité
            new_word = self.get_synonym(word)
            if new_word != word:
                words[i] = new_word
        
        return ' '.join(words)

    def generate_variant(self, sentence):
        """Génère une variante de la phrase en appliquant des modifications aléatoires."""
        if not sentence.strip():
            return sentence
            
        techniques = [
            # Changer la ponctuation
            lambda s: s.replace('.', '...') if '.' in s and random.random() > 0.7 else s,
            lambda s: s.replace('?', '!') if '?' in s and random.random() > 0.7 else s,
            
            # Modifier la casse
            lambda s: s[0].lower() + s[1:] if len(s) > 0 and s[0].isupper() and random.random() > 0.7 else s,
            
            # Ajouter des points d'exclamation
            lambda s: s + '!' if not s.endswith('!') and random.random() > 0.7 else s,
            
            # Raccourcir la phrase
            lambda s: ' '.join(s.split()[:-1]) + '.' if len(s.split()) > 5 and random.random() > 0.8 else s
        ]
        
        # Appliquer 1 à 2 techniques aléatoires
        variant = sentence
        for _ in range(random.randint(1, 2)):
            variant = random.choice(techniques)(variant)
        
        # S'assurer que la phrase commence par une majuscule
        if variant and variant[0].islower():
            variant = variant[0].upper() + variant[1:]
            
        return variant

    def _get_improvement_description(self, improved_text, original_text):
        """Génère une description des améliorations apportées au texte."""
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
            # Nettoyer le texte d'entrée
            cleaned_text = self.clean_text(text).strip()
            if not any(cleaned_text.endswith(p) for p in ['.', '!', '?']):
                cleaned_text += '.'
            if cleaned_text and cleaned_text[0].islower():
                cleaned_text = cleaned_text[0].upper() + cleaned_text[1:]
            
            # Découper en phrases
            sentences = sent_tokenize(cleaned_text, language='french')
            
            # Version 1 : Amélioration simple
            improved_sentences = [self.improve_sentence(s) for s in sentences]
            version1 = ' '.join(improved_sentences)
            
            # Version 2 : Variante avec des phrases mélangées (si plus d'une phrase)
            version2 = None
            if len(sentences) > 1:
                mixed = sentences.copy()
                random.shuffle(mixed)
                version2 = ' '.join(self.improve_sentence(s) for s in mixed)
            
            # Version 3 : Variante avec des connecteurs différents
            version3 = None
            if len(sentences) > 1:
                variant = []
                for sent in sentences:
                    if random.random() > 0.5:
                        variant.append(self.generate_variant(sent))
                    else:
                        variant.append(self.improve_sentence(sent))
                version3 = ' '.join(variant)
            
            # Préparer les versions uniques
            versions = []
            for v in [version1, version2, version3]:
                if v and v != cleaned_text and v not in versions:
                    versions.append(self.clean_text(v))
            
            # Si aucune version n'est générée, utiliser l'originale améliorée
            if not versions:
                versions = [self.improve_sentence(cleaned_text)]
            
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
