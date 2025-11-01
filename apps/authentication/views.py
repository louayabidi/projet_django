# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

# Create your views here.
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login

from apps.authentication.models import User
from apps.book.models import Book
from .forms import LoginForm, SignUpForm


def login_view(request):
    form = LoginForm(request.POST or None)

    msg = None

    if request.method == "POST":

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if hasattr(user, 'role') and user.role == "admin":
                    return redirect("/dashboard/")  # admin
                else:
                    return redirect("/")
            else:
                msg = 'Invalid credentials'
        else:
            msg = 'Error validating the form'

    return render(request, "accounts/login.html", {"form": form, "msg": msg})


def register_user(request):
    msg = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                username = form.cleaned_data.get("username")
                raw_password = form.cleaned_data.get("password1")
                user = authenticate(username=username, password=raw_password)

                msg = 'User created - please <a href="/login">login</a>.'
                success = True

                # return redirect("/login/")

            except Exception as e:
                msg = f'Error creating user: {str(e)}'
        else:
            msg = 'Form is not valid'
    else:
        form = SignUpForm()

    return render(request, "accounts/register.html", {"form": form, "msg": msg, "success": success})
def user_books(request, user_id):
    # Récupérer l'utilisateur cible
    user = get_object_or_404(User, id=user_id)
    # Filtrer les livres de cet utilisateur
    books = Book.objects.filter(author=user)
    return render(request, "accounts/profile.html", {"books": books, "profile_user": user})


