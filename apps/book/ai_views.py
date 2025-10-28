from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import json
from .ai_service import ai_service

@login_required
@require_http_methods(["POST"])
def correct_grammar(request):
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        
        if not text:
            return JsonResponse({'success': False, 'error': 'Texte vide'}, status=400)
        
        result = ai_service.correct_grammar(text)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def generate_synopsis(request):
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        
        if not text:
            return JsonResponse({'success': False, 'error': 'Texte vide'}, status=400)
        
        result = ai_service.generate_synopsis(text)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def analyze_sentiment(request):
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        
        if not text:
            return JsonResponse({'success': False, 'error': 'Texte vide'}, status=400)
        
        result = ai_service.analyze_sentiment(text)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def extract_keywords(request):
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        
        if not text:
            return JsonResponse({'success': False, 'error': 'Texte vide'}, status=400)
        
        result = ai_service.extract_keywords(text)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def detect_genre(request):
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        
        if not text:
            return JsonResponse({'success': False, 'error': 'Texte vide'}, status=400)
        
        result = ai_service.detect_genre(text)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def analyze_readability(request):
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        
        if not text:
            return JsonResponse({'success': False, 'error': 'Texte vide'}, status=400)
        
        result = ai_service.analyze_readability(text)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def full_analysis(request):
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        
        if not text:
            return JsonResponse({'success': False, 'error': 'Texte vide'}, status=400)
        
        result = ai_service.full_analysis(text)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# === GENERATION ENDPOINTS (Hugging Face) ===
@login_required
@require_http_methods(["POST"])
def suggest_continue(request):
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        params = data.get('params', {})
        if not text:
            return JsonResponse({'success': False, 'error': 'Texte vide'}, status=400)
        result = ai_service.suggest_continue(
            text,
            max_new_tokens=int(params.get('max_new_tokens', 80)),
            num_return_sequences=int(params.get('num_return_sequences', 3)),
            temperature=float(params.get('temperature', 0.9)),
            top_p=float(params.get('top_p', 0.95)),
        )
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def rewrite_text(request):
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        style = data.get('style', 'simple')
        if not text:
            return JsonResponse({'success': False, 'error': 'Texte vide'}, status=400)
        result = ai_service.rewrite_text(text, style=style, max_new_tokens=int(data.get('max_new_tokens', 120)))
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def suggest_titles(request):
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        num_titles = int(data.get('num_titles', 5))
        if not text:
            return JsonResponse({'success': False, 'error': 'Texte vide'}, status=400)
        result = ai_service.suggest_titles(text, num_titles=num_titles)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
