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
from apps.book.models import Book
from django.shortcuts import render


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