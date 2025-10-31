# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import redirect
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.models import User
from apps.book.models import Book
from django.contrib.auth import get_user_model
User = get_user_model()
@login_required(login_url="/login/")
def index(request):
    context = {'segment': 'index'}

    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:

        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))


# ---------------------------------------
# Admin Book Management Views
# ---------------------------------------

@login_required(login_url="/login/")
def admin_books_list(request):
    """
    Vue pour les admins: affiche tous les livres de tous les artistes
    Les admins peuvent seulement voir, pas modifier ni supprimer
    """
    # Vérifier que l'utilisateur est un admin
    if request.user.role != 'admin':
        messages.error(request, "Accès refusé. Cette section est réservée aux administrateurs.")
        return redirect('home')
    
    # Récupérer tous les livres avec les informations de l'auteur
    books = Book.objects.all().select_related('author').order_by('-created_at')
    
    context = {
        'segment': 'admin-books',
        'books': books,
        'total_books': books.count()
    }
    
    html_template = loader.get_template('home/admin-books-list.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def admin_book_detail(request, id):
    """
    Vue détaillée d'un livre pour les admins (lecture seule)
    """
    # Vérifier que l'utilisateur est un admin
    if request.user.role != 'admin':
        messages.error(request, "Accès refusé. Cette section est réservée aux administrateurs.")
        return redirect('home')
    
    from django.shortcuts import get_object_or_404
    book = get_object_or_404(Book, id=id)
    
    context = {
        'segment': 'admin-books',
        'book': book
    }
    
    html_template = loader.get_template('home/admin-book-detail.html')
    return HttpResponse(html_template.render(context, request))


@login_required
def dashboard_view(request):
    # ici tu peux ajouter d'autres contextes si nécessaire
    return render(request, "home/dashboard.html")
@login_required
def search(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})

    results = []

    # Search Books
    books = Book.objects.filter(title__icontains=query)[:5]
    for book in books:
        if book.status == 'termine' or book.status == 'archive':  # Only include completed or archived books
            results.append({
                'type': 'Book',
                'name': book.title,
                'url': book.get_absolute_url() if hasattr(book, 'get_absolute_url') else '#',
                
            })

    # Search Users (custom user model)
    users = User.objects.filter(username__icontains=query)[:5]
    for user in users:
        results.append({
            'type': 'User',
            'name': user.username,
            'url': f'/user/{user.id}/',  # Adjust to your user detail page
        })

    return JsonResponse({'results': results})