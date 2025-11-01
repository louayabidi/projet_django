import random
from django.db import models
from django.contrib.auth import get_user_model
from apps.book.models import Book 
from apps.collaboration.models import CollaborationPost, CollaborationResponse
from faker import Faker
from django.utils import timezone
import os
import django
import csv

# Configurer Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

fake = Faker()
User = get_user_model()

NUM_USERS = 50           # nombre d'utilisateurs
NUM_BOOKS = 200          # nombre de livres
NUM_COLLAB_POSTS = 100   # nombre de posts de collaboration
NUM_RESPONSES = 300      # nombre de réponses

genres = ['Roman', 'Science-fiction', 'Fantaisie', 'Horreur', 'Poésie', 'Romance']

# 1️⃣ Création des utilisateurs
users = []
for _ in range(NUM_USERS):
    user = User.objects.create_user(
        username=fake.unique.user_name(),
        email=fake.email(),
        password='password123',
        role='artist'
    )
    users.append(user)

# 2️⃣ Création des livres
books = []
for _ in range(NUM_BOOKS):
    author = random.choice(users)
    book = Book.objects.create(
        title=fake.sentence(nb_words=4),
        synopsis=fake.paragraph(nb_sentences=5),
        genre=random.choice(genres),
        status=random.choice(['en_cours', 'termine', 'archive']),
        author=author,
        content=fake.text(max_nb_chars=1000)
    )
    collaborators = random.sample(users, k=random.randint(0, 3))
    for collab in collaborators:
        if collab != author:
            book.collaborators.add(collab)
    books.append(book)

# 3️⃣ Création de posts de collaboration
collab_posts = []
for _ in range(NUM_COLLAB_POSTS):
    author = random.choice(users)
    book = random.choice(books)
    post = CollaborationPost.objects.create(
        author=author,
        book=book,
        title=fake.sentence(nb_words=6),
        content=fake.paragraph(nb_sentences=3),
        created_at=fake.date_time_this_year(before_now=True, after_now=False, tzinfo=timezone.utc)
    )
    collab_posts.append(post)

# 4️⃣ Création de réponses aux posts
for _ in range(NUM_RESPONSES):
    post = random.choice(collab_posts)
    responder = random.choice(users)
    if responder != post.author:
        status = random.choices(['pending', 'accepted', 'refused'], weights=[0.4, 0.4, 0.2])[0]
        CollaborationResponse.objects.create(
            post=post,
            responder=responder,
            message=fake.paragraph(nb_sentences=2),
            status=status,
            created_at=fake.date_time_this_year(before_now=True, after_now=False, tzinfo=timezone.utc)
        )

print("✅ Données fictives générées dans la base de données.")
