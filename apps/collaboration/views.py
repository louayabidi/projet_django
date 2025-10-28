from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CollaborationPost, CollaborationResponse
from .forms import CollaborationPostForm, CollaborationResponseForm
from django.contrib import messages
from .models import Book
# Liste des posts
@login_required
def collaborations_list(request):
    posts = CollaborationPost.objects.all().order_by('-created_at')
    return render(request, 'collaboration/collaborations.html', {'posts': posts})

@login_required
def collaboration_detail(request, post_id):
    post = get_object_or_404(CollaborationPost, id=post_id)
    return render(request, 'collaboration/collaboration_detail.html', {'post': post})

# Créer un post de collaboration
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
        form = CollaborationPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('collaborations_list')
    else:
        form = CollaborationPostForm(instance=post)
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