# apps/forum/ai_response_generator.py
from transformers import pipeline,AutoTokenizer, AutoModelForCausalLM,BlenderbotTokenizer, BlenderbotForConditionalGeneration
import logging
import re
import torch

logger = logging.getLogger(__name__)

class AIResponseGenerator:
    def __init__(self, model_name="facebook/blenderbot-400M-distill", device=None):
        """
        Initialisation du modèle BlenderBot (léger, adapté CPU).
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # Charger tokenizer et modèle
        self.tokenizer = BlenderbotTokenizer.from_pretrained(model_name)
        self.model = BlenderbotForConditionalGeneration.from_pretrained(model_name).to(self.device)

        # Définir une longueur maximale sûre pour ce modèle
        self.max_input_tokens = 120

    def truncate_input(self, text):
        """
        Tronque le texte si trop long pour le modèle.
        """
        tokens = self.tokenizer.tokenize(text)
        if len(tokens) > self.max_input_tokens:
            tokens = tokens[-self.max_input_tokens:]
        return self.tokenizer.convert_tokens_to_string(tokens)

    def generate_responses(self, text, num_responses=3, max_new_tokens=60):
        """
        Génère jusqu'à `num_responses` réponses pour `text`.
        Renvoie une liste de chaînes (fallback si vide).
        """
        responses = []
        try:
            # Tronquer l'entrée si elle est trop longue
            truncated_text = self.truncate_input(text.strip())

            # Prépare un prompt demandant une réponse courte et dans la même langue
            prompt = f"Réponds brièvement et poliment dans la même langue que ce texte : {truncated_text}"

            # Tokenize et envoyer sur device
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=self.max_input_tokens)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            for i in range(num_responses):
                output_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=True,
                    top_k=60,
                    top_p=0.9,
                    temperature=0.8 + (i * 0.05),
                    repetition_penalty=1.1,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )

                response = self.tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()

                if response and len(response) > 5:
                    # Supprime le prompt éventuel
                    if prompt in response:
                        response = response.replace(prompt, "").strip()
                    responses.append(response)

        except Exception as e:
            print(f"⚠️ Erreur génération IA: {e}")

        if not responses:
            responses = [
                "Je te conseille d’ajouter plus de détails à ton post pour obtenir une réponse plus précise.",
                "Peux-tu préciser ce point ? Cela aidera la communauté à mieux t'aider.",
                "Ton sujet est intéressant — pourrais-tu ajouter un exemple concret ?"
            ]

        return responses[:num_responses]

    def _create_prompt(self, post_content):
        """Crée un prompt contextuel pour le modèle"""
        truncated_content = post_content[:300] + "..." if len(post_content) > 300 else post_content
        
        prompt = f"""En tant qu'expert littéraire, répondez brièvement et intelligemment à cette discussion :

"{truncated_content}"

Réponse :"""
        
        return prompt

    def _clean_response(self, generated_text, prompt):
        """Nettoie et formate la réponse générée"""
        try:
            # Supprimer le prompt de la réponse
            if prompt in generated_text:
                response = generated_text.replace(prompt, "").strip()
            else:
                response = generated_text.strip()
            
            # Nettoyer
            response = re.sub(r'\s+', ' ', response)
            response = re.sub(r'^(?:Human:|AI:|\d+\.\s*)\s*', '', response)
            
            if not response or len(response) < 10:
                return None
            
            # Formater
            response = response[0].upper() + response[1:]
            if not response.endswith(('.', '!', '?')):
                response += '.'
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"❌ Erreur nettoyage réponse: {e}")
            return None

    def _get_fallback_responses(self):
        """Réponses de fallback si l'IA échoue"""
        return [
            "Cette discussion soulève des points très intéressants sur la littérature contemporaine.",
            "Je trouve votre analyse particulièrement pertinente dans le contexte actuel.",
            "Votre perspective ouvre des pistes de réflexion passionnantes pour les amateurs de littérature.",
            "Excellente contribution qui enrichit considérablement notre débat littéraire.",
            "Votre point de vue mérite d'être approfondi, car il touche à des enjeux fondamentaux."
        ]

# Instance globale
ai_response_generator = AIResponseGenerator()