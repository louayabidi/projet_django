from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import json
from .ai_service import ai_service
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .utils import check_web_plagiarism

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
    



@csrf_exempt
@require_POST
def check_web_plagiarism_view(request):
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()

        if not text:
            return JsonResponse({'error': 'Texte vide'}, status=400)

        if len(text) < 50:
            return JsonResponse({'error': 'Texte trop court'}, status=400)

        # UTILISE LA BONNE FONCTION
        matches = check_web_plagiarism(text)

        return JsonResponse({
            'success': True,
            'matches': matches
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON invalide'}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)