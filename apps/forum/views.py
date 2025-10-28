# apps/forum/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Post, Comment
from .forms import PostForm, CommentForm
from .toxicity_detector import toxicity_detector
from .summarizer import discussion_summarizer  

def post_list(request):
    posts = Post.objects.all()
    total_comments = Comment.objects.count()
    
    # Ajouter les résumés aux posts longs
    for post in posts:
        post.has_summary = discussion_summarizer.should_summarize(post.content)
    
    return render(request, 'forum/post_list.html', {
        'posts': posts,
        'total_comments': total_comments
    })

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all()
    
    # Générer le résumé pour l'affichage
    summary = None
    if discussion_summarizer.should_summarize(post.content):
        summary = discussion_summarizer.summarize_text(post.content)
    
    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            content = comment_form.cleaned_data['content']
            
            # Vérifier la toxicité
            toxicity_score = toxicity_detector.analyze_toxicity(content)
            
            if toxicity_score >= 0.7:
                messages.error(
                    request, 
                    f"Commentaire détecté comme inapproprié (score: {toxicity_score:.2f})."
                )
                return render(request, 'forum/post_detail.html', {
                    'post': post,
                    'comments': comments,
                    'comment_form': comment_form,
                    'toxicity_score': toxicity_score,
                    'summary': summary
                })
            else:
                comment = comment_form.save(commit=False)
                comment.post = post
                comment.author = request.user
                comment.save()
                
                messages.success(request, "Commentaire publié!")
                return redirect('forum:post_detail', pk=post.pk)
    else:
        comment_form = CommentForm()
    
    return render(request, 'forum/post_detail.html', {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'summary': summary
    })

@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            # Optionnel: vérifier aussi la toxicité des posts
            content = form.cleaned_data['content']
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
            messages.success(request, 'Votre discussion a été créée!')
            return redirect('forum:post_detail', pk=post.pk)
    else:
        form = PostForm()
    
    return render(request, 'forum/post_form.html', {
        'form': form,
        'title': 'Créer une discussion'
    })

@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            # Vérifier la toxicité de l'édition
            content = form.cleaned_data['content']
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
            messages.success(request, 'Votre discussion a été modifiée!')
            return redirect('forum:post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    
    return render(request, 'forum/post_form.html', {
        'form': form,
        'title': 'Modifier la discussion'
    })

@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    
    if request.method == 'POST':
        post_title = post.title
        post.delete()
        messages.success(request, f'La discussion "{post_title}" a été supprimée!')
        return redirect('forum:post_list')
    
    return render(request, 'forum/post_confirm_delete.html', {'post': post})