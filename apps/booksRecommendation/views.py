from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.book.models import Book
from .models import UserInteraction
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
import numpy as np
from django.contrib.auth import get_user_model
User = get_user_model()
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

def get_book_recommendations(book_id, top_n=5):
    # Récupérer tous les livres depuis la base
    books = Book.objects.all()
    
    # Construire un DataFrame
    df = pd.DataFrame(list(books.values('id', 'title', 'content', 'genre')))
    
    # Combiner contenu et genre pour enrichir le texte
    df['combined'] = df['content'] + ' ' + df['genre']
    
    # TF-IDF
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df['combined'])
    
    # Calculer similarité cosine
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    # Trouver l'index du livre donné
    idx = df.index[df['id'] == book_id].tolist()[0]
    
    # Trier les livres similaires
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:top_n+1]  # exclure le livre lui-même
    
    # Récupérer les IDs
    book_indices = [i[0] for i in sim_scores]
    return Book.objects.filter(id__in=df.iloc[book_indices]['id'].values)
def build_interaction_matrix():
    user_book_data = []

    for user in User.objects.all():
        for book in user.favorite_books.all():
            user_book_data.append((user.id, book.id, 1))

    # <--- Ajouter le print ici
    print("User-Book Data:", user_book_data)

    df = pd.DataFrame(user_book_data, columns=['user_id', 'book_id', 'interaction'])
    if df.empty:
        return pd.DataFrame()  # Aucun favori

    user_book_matrix = df.pivot(index='user_id', columns='book_id', values='interaction').fillna(0)
    return user_book_matrix


def train_knn_model(user_book_matrix):
    if user_book_matrix.empty:
        return None

    model = NearestNeighbors(metric='cosine', algorithm='brute')
    model.fit(user_book_matrix)
    return model

def get_user_recommendations(user_id, top_n=5):
    user_book_matrix = build_interaction_matrix()
    if user_book_matrix.empty or user_id not in user_book_matrix.index:
        return []

    model = train_knn_model(user_book_matrix)

    # ne pas dépasser le nombre d'utilisateurs existants
    n_neighbors = min(top_n + 1, len(user_book_matrix))

    distances, indices = model.kneighbors(
        [user_book_matrix.loc[user_id].values], n_neighbors=n_neighbors
    )

    neighbor_ids = [user_book_matrix.index[i] for i in indices[0] if user_book_matrix.index[i] != user_id]

    recommended_books_ids = []
    for neighbor in neighbor_ids:
        neighbor_books = user_book_matrix.loc[neighbor]
        unseen_books = neighbor_books[(neighbor_books > 0) & (user_book_matrix.loc[user_id] == 0)].index.tolist()
        recommended_books_ids.extend(unseen_books)

    recommended_books_ids = list(dict.fromkeys(recommended_books_ids))[:top_n]
    return Book.objects.filter(id__in=recommended_books_ids)

