from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.book.models import Book
from .models import UserInteraction

@login_required
def recommended_books(request):
    user = request.user
    interactions = UserInteraction.objects.filter(user=user)

    genre_scores = {}
    for interaction in interactions:
        points = 0
        if interaction.viewed:
            points += 1
        if interaction.added_to_cart:
            points += 2
        if interaction.favorited:
            points += 3
        genre = interaction.book.genre
        genre_scores[genre] = genre_scores.get(genre, 0) + points

    favorite_genres = sorted(genre_scores, key=genre_scores.get, reverse=True)

    recommended_books = Book.objects.filter(
        genre__in=favorite_genres
    ).exclude(
        userinteraction__user=user
    ).distinct()[:10]

    context = {
        "recommended_books": recommended_books,
        "favorite_genres": favorite_genres,
    }
    return render(request, "booksRecommendation/recommended_books.html", context)

