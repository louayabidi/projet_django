# apps/forum/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Post, Comment
from .forms import PostForm, CommentForm

# ===== IMPORTS DES SERVICES IA =====

# Summarizer
try:
    from .summarizer import discussion_summarizer
    SUMMARIZER_AVAILABLE = True
    print(" Summarizer chargé")
except ImportError as e:
    print(f" Summarizer non disponible: {e}")
    SUMMARIZER_AVAILABLE = False
    
    class BasicSummarizer:
        def should_summarize(self, text):
            return len(text.split()) > 80 if text else False
        
        def summarize_text(self, text, max_length=150, min_length=50):
            if not text:
                return ""
            if len(text) <= max_length:
                return text
            return text[:max_length-3] + '...'
    
    discussion_summarizer = BasicSummarizer()

# Toxicity Detector
try:
    from .toxicity_detector import toxicity_detector
    TOXICITY_DETECTOR_AVAILABLE = True
    print(" Toxicity detector chargé")
except ImportError:
    print(" Toxicity detector non disponible")
    TOXICITY_DETECTOR_AVAILABLE = False
    
    class BasicToxicityDetector:
        def analyze_toxicity(self, text):
            # Détection basique de mots interdits
            toxic_words = ['stupide', 'idiot', 'imbécile', 'connard', 'merde', 'salop', 'putain']
            if any(word in text.lower() for word in toxic_words):
                return 0.8
            return 0.1
    
    toxicity_detector = BasicToxicityDetector()

# AI Response Generator
try:
    from .ai_response_generator import ai_response_generator
    AI_RESPONSE_AVAILABLE = True
    print(" Générateur de réponses IA chargé")
except ImportError as e:
    print(f" Générateur IA non disponible: {e}")
    AI_RESPONSE_AVAILABLE = False
    
    # Fallback basique
    class BasicResponseGenerator:
        def generate_responses(self, post_content, num_responses=3, max_length=100):
            return [
                "Cette discussion soulève des points très intéressants sur la littérature contemporaine.",
                "Je trouve votre analyse particulièrement pertinente dans le contexte actuel.",
                "Votre perspective ouvre des pistes de réflexion passionnantes pour les amateurs de littérature.",
                "Excellente contribution qui enrichit considérablement notre débat littéraire.",
            ][:num_responses]
    
    ai_response_generator = BasicResponseGenerator()

# ===== VUES =====

def post_list(request):
    """Liste toutes les discussions du forum"""
    posts = Post.objects.all()
    total_comments = Comment.objects.count()
    
    # Préparer les données pour le template
    for post in posts:
        if SUMMARIZER_AVAILABLE:
            post.has_summary = discussion_summarizer.should_summarize(post.content)
            if post.has_summary:
                post.summary = discussion_summarizer.summarize_text(post.content)
        else:
            # Fallback si summarizer non disponible
            post.has_summary = len(post.content.split()) > 80 if post.content else False
            if post.has_summary and post.content:
                post.summary = post.content[:147] + '...' if len(post.content) > 150 else post.content
        
        post.word_count = len(post.content.split()) if post.content else 0
    
    return render(request, 'forum/post_list.html', {
        'posts': posts,
        'total_comments': total_comments
    })

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all()
    
    # Générer le résumé
    summary = None
    if SUMMARIZER_AVAILABLE:
        if discussion_summarizer.should_summarize(post.content):
            summary = discussion_summarizer.summarize_text(post.content)
    
    # Générer des réponses IA - APPEL CORRIGÉ
    ai_responses = []
    if AI_RESPONSE_AVAILABLE and post.content:
        try:
            # SEULEMENT num_responses, pas de max_length
            ai_responses = ai_response_generator.generate_responses(
                post.content, 
                num_responses=3
            )
            print(f"🎯 {len(ai_responses)} réponses IA générées")
        except Exception as e:
            print(f"❌ Erreur génération réponses IA: {e}")
            ai_responses = []
    
    # ===== GESTION DES COMMENTAIRES =====
    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            content = comment_form.cleaned_data['content']
            
            # Vérifier la toxicité
            toxicity_score = 0.1  # Valeur par défaut safe
            if TOXICITY_DETECTOR_AVAILABLE:
                toxicity_score = toxicity_detector.analyze_toxicity(content)
            
            if toxicity_score >= 0.7:
                messages.error(
                    request, 
                    f"Commentaire détecté comme inapproprié (score: {toxicity_score:.2f}). "
                    "Veuillez reformuler votre message."
                )
                return render(request, 'forum/post_detail.html', {
                    'post': post,
                    'comments': comments,
                    'comment_form': comment_form,
                    'toxicity_score': toxicity_score,
                    'summary': summary,
                    'ai_responses': ai_responses
                })
            else:
                # Commentaire acceptable
                comment = comment_form.save(commit=False)
                comment.post = post
                comment.author = request.user
                comment.save()
                
                messages.success(request, "Votre commentaire a été publié avec succès!")
                return redirect('forum:post_detail', pk=post.pk)
    else:
        comment_form = CommentForm()
    
    return render(request, 'forum/post_detail.html', {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'summary': summary,
        'ai_responses': ai_responses,
        'toxicity_score': None  # Reset pour les requêtes GET
    })

@login_required
def post_create(request):
    """Création d'une nouvelle discussion"""
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            # Vérifier la toxicité du post
            content = form.cleaned_data['content']
            toxicity_score = 0.1
            if TOXICITY_DETECTOR_AVAILABLE:
                toxicity_score = toxicity_detector.analyze_toxicity(content)
            
            if toxicity_score >= 0.7:
                messages.error(
                    request,
                    f"Votre publication a été détectée comme inappropriée (score: {toxicity_score:.2f}). "
                    "Veuillez reformuler votre message."
                )
                return render(request, 'forum/post_form.html', {
                    'form': form,
                    'title': 'Créer une discussion'
                })
            
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            
            messages.success(request, 'Votre discussion a été créée avec succès!')
            return redirect('forum:post_detail', pk=post.pk)
    else:
        form = PostForm()
    
    return render(request, 'forum/post_form.html', {
        'form': form,
        'title': 'Créer une discussion'
    })

@login_required
def post_edit(request, pk):
    """Modification d'une discussion existante"""
    post = get_object_or_404(Post, pk=pk, author=request.user)
    
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            # Vérifier la toxicité de l'édition
            content = form.cleaned_data['content']
            toxicity_score = 0.1
            if TOXICITY_DETECTOR_AVAILABLE:
                toxicity_score = toxicity_detector.analyze_toxicity(content)
            
            if toxicity_score >= 0.7:
                messages.error(
                    request,
                    f"Votre modification a été détectée comme inappropriée (score: {toxicity_score:.2f})."
                )
                return render(request, 'forum/post_form.html', {
                    'form': form,
                    'title': 'Modifier la discussion'
                })
            
            form.save()
            messages.success(request, 'Votre discussion a été modifiée avec succès!')
            return redirect('forum:post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    
    return render(request, 'forum/post_form.html', {
        'form': form,
        'title': 'Modifier la discussion'
    })

@login_required
def post_delete(request, pk):
    """Suppression d'une discussion"""
    post = get_object_or_404(Post, pk=pk, author=request.user)
    
    if request.method == 'POST':
        post_title = post.title
        post.delete()
        messages.success(request, f'La discussion "{post_title}" a été supprimée avec succès!')
        return redirect('forum:post_list')
    
    return render(request, 'forum/post_confirm_delete.html', {'post': post})