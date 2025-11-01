from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import CollaborationPost, CollaborationResponse, Book
from .forms import CollaborationPostForm, CollaborationResponseForm
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()


# Fonction de vérification admin
def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

# --- PAGES UTILISATEUR ---

@login_required
def collaborations_list(request):
    posts = CollaborationPost.objects.all().order_by('-created_at')
    return render(request, 'collaboration/collaborations.html', {'posts': posts})



@login_required
def create_collaboration_post(request):
    if request.method == 'POST':
        form = CollaborationPostForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('collaborations_list')
    else:
        form = CollaborationPostForm(user=request.user)
    
    return render(request, 'collaboration/create_post.html', {'form': form})

@login_required
def update_collaboration_post(request, post_id):
    post = get_object_or_404(CollaborationPost, id=post_id, author=request.user)

    if request.method == 'POST':
        form = CollaborationPostForm(request.POST, request.FILES, instance=post, user=request.user)
        if form.is_valid():

            # Supprimer l'image si demandé
            if request.POST.get('image-clear') and post.image:
                post.image.delete()
                post.image = None

            # Mettre à jour l'image si nouvelle uploadée
            if request.FILES.get('image'):
                post.image = request.FILES['image']

            # Mettre à jour les autres champs
            post.title = form.cleaned_data['title']
            post.content = form.cleaned_data['content']
            post.book = form.cleaned_data['book']

            post.save()

            messages.success(request, "Collaboration mise à jour avec succès !")
            return redirect('collaboration_detail', post_id=post.id)
        else:
            messages.error(request, "Erreur dans le formulaire. Vérifiez vos champs.")
    else:
        form = CollaborationPostForm(instance=post, user=request.user)

    return render(request, 'collaboration/update_post.html', {'form': form, 'post': post})



@login_required
def delete_collaboration_post(request, post_id):
    post = get_object_or_404(CollaborationPost, id=post_id, author=request.user)
    if request.method == 'POST':
        post.delete()
        return redirect('collaborations_list')
    return render(request, 'collaboration/delete_post.html', {'post': post})


# Répondre à un post
@login_required
def respond_to_collaboration(request, post_id):
    post = get_object_or_404(CollaborationPost, id=post_id)
    if request.method == 'POST':
        form = CollaborationResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.post = post
            response.responder = request.user
            response.save()
            return redirect('collaborations_list')
    else:
        form = CollaborationResponseForm()
    return render(request, 'collaboration/respond_post.html', {'form': form, 'post': post})

# Gérer les réponses (accepter/refuser)
@login_required
def update_response_status(request, response_id, status):
    response = get_object_or_404(CollaborationResponse, id=response_id, post__author=request.user)
    response.status = status
    response.save()
    return redirect('collaborations_list')




@login_required
def respond_to_collaboration(request, post_id):
    post = get_object_or_404(CollaborationPost, id=post_id)
    if request.method == 'POST':
        form = CollaborationResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.post = post
            response.responder = request.user
            response.save()
            return redirect('collaborations_list')
    else:
        form = CollaborationResponseForm()
    return render(request, 'collaboration/respond_post.html', {'form': form, 'post': post})


# --- AFFICHER LES RÉPONSES D’UN POST ---
@login_required
def responses_list(request, post_id):
    post = get_object_or_404(CollaborationPost, id=post_id)
    responses = post.responses.all().order_by('-created_at')
    return render(request, 'collaboration/responses_list.html', {'post': post, 'responses': responses})


# --- MODIFIER UNE RÉPONSE ---
@login_required
def update_response(request, response_id):
    response = get_object_or_404(CollaborationResponse, id=response_id, responder=request.user)
    if request.method == 'POST':
        form = CollaborationResponseForm(request.POST, instance=response)
        if form.is_valid():
            form.save()
            return redirect('responses_list', post_id=response.post.id)
    else:
        form = CollaborationResponseForm(instance=response)
    return render(request, 'collaboration/update_response.html', {'form': form, 'response': response})


# --- SUPPRIMER UNE RÉPONSE ---
@login_required
def delete_response(request, response_id):
    response = get_object_or_404(CollaborationResponse, id=response_id, responder=request.user)
    if request.method == 'POST':
        response.delete()
        return redirect('responses_list', post_id=response.post.id)
    return render(request, 'collaboration/delete_response.html', {'response': response})


# --- CHANGER STATUT PAR AUTEUR DU POST ---
@login_required
def update_response_status(request, response_id, status):
    response = get_object_or_404(CollaborationResponse, id=response_id, post__author=request.user)
    response.status = status
    response.save()
    return redirect('responses_list', post_id=response.post.id)


@login_required
def update_response_status(request, response_id, status):
    response = get_object_or_404(CollaborationResponse, id=response_id)

    # Vérification: seul l'auteur du post peut accepter/refuser
    if request.user != response.post.author:
        messages.error(request, "Vous n'êtes pas autorisé à gérer cette réponse.")
        return redirect('collaboration_detail', post_id=response.post.id)

    response.status = status
    response.save()

    if status == 'accepted':
        book = response.post.book
        book.collaborators.add(response.responder)
        book.save()
        messages.success(request, f"{response.responder.username} a été ajouté comme collaborateur sur le livre.")

    else:
        messages.info(request, f"La réponse de {response.responder.username} a été {status}.")

    return redirect('collaboration_detail', post_id=response.post.id)
# --- PAGES ADMIN ---

@login_required
@user_passes_test(is_admin)
def admin_collaborations(request):
    posts = CollaborationPost.objects.all().order_by('-created_at')
    
    total_posts = posts.count()
    total_responses = CollaborationResponse.objects.count()
    pending_responses = CollaborationResponse.objects.filter(status='pending').count()
    accepted_responses = CollaborationResponse.objects.filter(status='accepted').count()
    
    context = {
        'posts': posts,
        'total_posts': total_posts,
        'total_responses': total_responses,
        'pending_responses': pending_responses,
        'accepted_responses': accepted_responses,
    }
    
    return render(request, 'collaboration/admin-collaboration.html', context)

@login_required
@user_passes_test(is_admin)
def admin_collaboration_responses(request, post_id):
    post = get_object_or_404(CollaborationPost, id=post_id)
    responses = post.responses.all().order_by('-created_at')
    
    accepted_count = responses.filter(status='accepted').count()
    pending_count = responses.filter(status='pending').count()
    refused_count = responses.filter(status='refused').count()
    
    context = {
        'post': post,
        'responses': responses,
        'accepted_count': accepted_count,
        'pending_count': pending_count,
        'refused_count': refused_count,
    }
    
    return render(request, 'collaboration/admin-collaboration-responses.html', context)


def recommend_artists_for_post(post, top_n=5):
    # ✅ Tous les artistes qui ont répondu à ce post (peu importe status)
    responses = post.responses.all()  
    candidates = set(resp.responder for resp in responses)

    recommendations = []

    for user in candidates:
        score = 0
        
        # ✅ Bonus simple: ils ont répondu
        score += 1  

        # ✅ Similarité de genre
        if post.book and hasattr(user, 'genres_authored') and post.book.genre:
            user_genres = set([g.strip().lower() for g in user.genres_authored.split(',')])
            book_genres = set([g.strip().lower() for g in post.book.genre.split(',')])
            
            genre_match = len(user_genres & book_genres)
            score += genre_match * 3

        # ✅ Collaborations passées réussies avec l'auteur du post
        past_collabs = CollaborationResponse.objects.filter(
            responder=user,
            post__author=post.author,
            status='accepted'
        ).count()
        score += past_collabs * 5

        # ✅ Expérience générale
        global_success = CollaborationResponse.objects.filter(
            responder=user,
            status='accepted'
        ).count()
        score += global_success * 2

        recommendations.append((user, score))

    # ✅ Trier par score décroissant
    recommendations.sort(key=lambda x: x[1], reverse=True)

    return recommendations[:top_n]


def fake_ai_text(user, post):
    # Tous les livres écrits par l'artiste
    books = Book.objects.filter(author=user)
    total_books = books.count()
    
    # Vérifier si l'artiste a déjà écrit dans le genre du post
    post_genre = post.book.genre.lower() if post.book and post.book.genre else None
    has_written_genre = False
    genres_written = set()
    
    for book in books:
        if book.genre:
            genres_written.add(book.genre.strip().lower())
    
    if post_genre:
        has_written_genre = post_genre in genres_written
    
    # Nombre de collaborations acceptées
    accepted_collabs = CollaborationResponse.objects.filter(
        responder=user,
        status='accepted'
    ).count()
    
    # Construire le résumé
    genre_text = f"a déjà écrit dans le genre '{post.book.genre}'" if has_written_genre else f"n'a pas encore écrit dans le genre '{post.book.genre}'"
    
    return (f" a écrit {total_books} livre(s), "
            f"a participé à {accepted_collabs} collaboration(s) acceptée(s), "
            f"et {genre_text}.")

@login_required
def collaboration_detail(request, post_id):
    post = get_object_or_404(CollaborationPost, id=post_id)
    
    # Recommandation
    recommended_artists = recommend_artists_for_post(post, top_n=5)

    # Texte AI fake pour chaque artiste recommandé
    for user, score in recommended_artists:
        user.ai_text = fake_ai_text(user, post)

    return render(request, 'collaboration/collaboration_detail.html', {
        'post': post,
        'recommended_artists': recommended_artists,
    })
