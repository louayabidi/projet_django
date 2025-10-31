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
        full_text = data.get('text', '').strip()
        context = data.get('context', '').strip()
        cursor_position = data.get('cursor_position', len(full_text))
        params = data.get('params', {})
        
        if not full_text:
            return JsonResponse({
                'success': False,
                'error': 'Aucun texte fourni',
                'suggestions': ["Commencez votre histoire..."]
            }, status=400)
        
        # Utiliser le contexte autour du curseur s'il est disponible
        text_to_analyze = context if context else full_text
        
        # Appeler le service IA avec les paramètres
        result = ai_service.suggest_continue(
            text=text_to_analyze,
            max_new_tokens=int(params.get('max_new_tokens', 80)),
            num_return_sequences=int(params.get('num_return_sequences', 3)),
            temperature=float(params.get('temperature', 0.9)),
            top_p=float(params.get('top_p', 0.95)),
        )
        
        # Ajouter des informations de débogage si nécessaire
        if request.GET.get('debug'):
            result['debug'] = {
                'context_used': text_to_analyze,
                'context_length': len(text_to_analyze),
                'cursor_position': cursor_position,
                'full_text_length': len(full_text)
            }
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Données JSON invalides',
            'suggestions': ["Erreur de format de données"]
        }, status=400)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur dans suggest_continue: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'success': False,
            'error': str(e),
            'suggestions': ["Une erreur est survenue lors de la génération"]
        }, status=500)


@login_required
@require_http_methods(["POST"])
def rewrite_text(request):
    """
    Vue pour la réécriture de texte avec des règles avancées.
    Ne nécessite plus de style spécifique, utilise une seule méthode de réécriture.
    """
    print("\n=== NOUVELLE REQUÊTE DE RÉÉCRITURE ===")
    
    try:
        # Récupération des données
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        max_tokens = int(data.get('max_new_tokens', 150))
        
        # Validation des entrées
        if not text:
            print("Erreur: Aucun texte fourni")
            return JsonResponse({
                'success': False, 
                'error': 'Veuillez fournir un texte à réécrire',
                'rewrites': []
            }, status=400)
        
        print(f"Texte à réécrire ({len(text)} caractères): {text[:200]}{'...' if len(text) > 200 else ''}")
        
        # Appel au service de réécriture
        result = ai_service.rewrite_text(text, max_new_tokens=max_tokens)
        
        # Journalisation du résultat
        if result.get('success'):
            print(f"Réécriture réussie. {len(result.get('rewrites', []))} suggestions générées")
            for i, rw in enumerate(result.get('rewrites', [])):
                rw_text = rw['text'] if isinstance(rw, dict) else rw
                print(f"Suggestion {i+1} ({len(rw_text)} caractères): {rw_text[:100]}...")
        else:
            print(f"Échec de la réécriture: {result.get('error', 'Erreur inconnue')}")
        
        # S'assurer que le format de la réponse est correct
        if 'rewrites' not in result:
            result['rewrites'] = []
        
        # Vérifier le format de chaque réécriture
        formatted_rewrites = []
        for rw in result['rewrites']:
            if isinstance(rw, str):
                formatted_rewrites.append({'text': rw, 'style': 'Amélioration'})
            elif isinstance(rw, dict) and 'text' in rw:
                formatted_rewrites.append(rw)
        
        result['rewrites'] = formatted_rewrites
        
        print(f"Format final de la réponse: {json.dumps(result, ensure_ascii=False)[:200]}...")
        
        response = JsonResponse(result)
        # Ajouter des en-têtes pour le débogage
        response['X-Debug-Text-Length'] = str(len(text))
        response['X-Debug-Rewrites-Count'] = str(len(formatted_rewrites))
        return response
        
    except json.JSONDecodeError as e:
        error_msg = f"Erreur de décodage JSON: {str(e)}"
        print(error_msg)
        return JsonResponse({
            'success': False,
            'error': 'Format de requête JSON invalide',
            'rewrites': []
        }, status=400)
        
    except Exception as e:
        import traceback
        error_msg = f"Erreur inattendue: {str(e)}\n{traceback.format_exc()}"
        print("\n" + "="*50)
        print("ERREUR DANS LA VUE REWRITE_TEXT")
        print("-"*50)
        print(error_msg)
        print("="*50 + "\n")
        
        return JsonResponse({
            'success': False,
            'error': f'Une erreur est survenue lors de la réécriture: {str(e)}',
            'rewrites': [],
            'debug': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def suggest_titles(request):
    try:
        print("Requête reçue pour la suggestion de titres")  # Debug log
        
        # Vérifier que les données sont au format JSON
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            print("Erreur: Données JSON invalides")  # Debug log
            return JsonResponse({'success': False, 'error': 'Format de données invalide'}, status=400)
        
        # Récupérer et valider les paramètres
        text = data.get('text', '').strip()
        if not text:
            print("Erreur: Texte vide")  # Debug log
            return JsonResponse({'success': False, 'error': 'Veuillez fournir du texte à analyser'}, status=400)
            
        try:
            num_titles = min(max(1, int(data.get('num_titles', 5))), 10)  # Entre 1 et 10 titres
        except (TypeError, ValueError):
            num_titles = 5
        
        print(f"Traitement de la demande pour {num_titles} titres")  # Debug log
        
        # Appeler le service d'IA
        result = ai_service.suggest_titles(text, num_titles=num_titles)
        
        # Vérifier que le résultat est valide
        if not result.get('success'):
            print(f"Erreur du service IA: {result.get('error', 'Erreur inconnue')}")  # Debug log
            
        return JsonResponse(result)
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Erreur inattendue: {error_trace}")  # Debug log
        return JsonResponse({
            'success': False, 
            'error': f'Une erreur est survenue lors de la génération des titres: {str(e)}'
        }, status=500)
