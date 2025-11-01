# apps/forum/ai_response_generator.py
from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration
import logging
import re
import torch

logger = logging.getLogger(__name__)

class AIResponseGenerator:
    def __init__(self, model_name="facebook/blenderbot-400M-distill"):
        """
        Initialize without loading model
        """
        self.model_name = model_name
        self.device = "cpu"  # Force CPU on free tier
        self._tokenizer = None
        self._model = None
        self.max_input_tokens = 120
        logger.info("AIResponseGenerator initialized (model will load on first use)")
    
    def _load_model(self):
        """Load model only when first needed"""
        if self._model is None:
            try:
                logger.info("🔄 Loading BlenderBot model for the first time...")
                
                self._tokenizer = BlenderbotTokenizer.from_pretrained(self.model_name)
                self._model = BlenderbotForConditionalGeneration.from_pretrained(
                    self.model_name
                ).to(self.device)
                
                logger.info("✅ Response generator loaded successfully")
            except Exception as e:
                logger.error(f"❌ Error loading response generator: {e}")
                self._model = None
                self._tokenizer = None
        
        return self._model is not None

    def truncate_input(self, text):
        """
        Truncate text if too long for the model
        """
        if not self._tokenizer:
            return text[:500]  # Fallback if tokenizer not loaded
        
        tokens = self._tokenizer.tokenize(text)
        if len(tokens) > self.max_input_tokens:
            tokens = tokens[-self.max_input_tokens:]
        return self._tokenizer.convert_tokens_to_string(tokens)

    def generate_responses(self, text, num_responses=3, max_new_tokens=60):
        """
        Generate up to num_responses for text (loads model on first call)
        Returns list of strings (fallback if empty)
        """
        responses = []
        
        try:
            # Load model on first use
            if not self._load_model():
                return self._get_fallback_responses()[:num_responses]
            
            # Truncate input if too long
            truncated_text = self.truncate_input(text.strip())

            # Prepare prompt asking for short, polite response
            prompt = f"Réponds brièvement et poliment dans la même langue que ce texte : {truncated_text}"

            # Tokenize and send to device
            inputs = self._tokenizer(
                prompt, 
                return_tensors="pt", 
                truncation=True, 
                max_length=self.max_input_tokens
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            for i in range(num_responses):
                output_ids = self._model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=True,
                    top_k=60,
                    top_p=0.9,
                    temperature=0.8 + (i * 0.05),
                    repetition_penalty=1.1,
                    pad_token_id=self._tokenizer.pad_token_id,
                    eos_token_id=self._tokenizer.eos_token_id,
                )

                response = self._tokenizer.decode(
                    output_ids[0], 
                    skip_special_tokens=True
                ).strip()

                if response and len(response) > 5:
                    # Remove prompt if present
                    if prompt in response:
                        response = response.replace(prompt, "").strip()
                    responses.append(response)

        except Exception as e:
            logger.error(f"⚠️ Erreur génération IA: {e}")

        if not responses:
            responses = self._get_fallback_responses()

        return responses[:num_responses]

    def _get_fallback_responses(self):
        """Fallback responses if AI fails"""
        return [
            "Cette discussion soulève des points très intéressants sur la littérature contemporaine.",
            "Je trouve votre analyse particulièrement pertinente dans le contexte actuel.",
            "Votre perspective ouvre des pistes de réflexion passionnantes pour les amateurs de littérature.",
            "Excellente contribution qui enrichit considérablement notre débat littéraire.",
            "Votre point de vue mérite d'être approfondi, car il touche à des enjeux fondamentaux.",
            "Je te conseille d'ajouter plus de détails à ton post pour obtenir une réponse plus précise.",
            "Peux-tu préciser ce point ? Cela aidera la communauté à mieux t'aider.",
            "Ton sujet est intéressant — pourrais-tu ajouter un exemple concret ?"
        ]

# Global instance (model loads lazily)
ai_response_generator = AIResponseGenerator()