# apps/forum/ai_config.py
import os

# Disable all AI features on free tier (512MB RAM insufficient)
ENABLE_AI_FEATURES = os.getenv('ENABLE_AI_FEATURES', 'False').lower() == 'true'

# Individual feature flags (for when you upgrade to paid tier)
ENABLE_SUMMARIZER = ENABLE_AI_FEATURES
ENABLE_TOXICITY_DETECTOR = ENABLE_AI_FEATURES
ENABLE_AI_RESPONSES = ENABLE_AI_FEATURES