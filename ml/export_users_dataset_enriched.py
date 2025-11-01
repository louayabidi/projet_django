import os
import django

# ⚡ Définir les settings avant tout import de modèles
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

import csv
from django.contrib.auth import get_user_model
from apps.book.models import Book
from apps.collaboration.models import CollaborationResponse

User = get_user_model()

with open('dataset_users_enriched.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['user_id','username','nbr_books_authored','genres_authored','nbr_books_collab','nbr_collab_accepted','nbr_collab_pending','nbr_collab_refused'])
    
    for user in User.objects.all():
        books_authored = Book.objects.filter(author=user)
        genres = list(set(book.genre for book in books_authored))
        nbr_books_authored = books_authored.count()
        nbr_books_collab = Book.objects.filter(collaborators=user).count()
        nbr_collab_accepted = CollaborationResponse.objects.filter(responder=user,status='accepted').count()
        nbr_collab_pending = CollaborationResponse.objects.filter(responder=user,status='pending').count()
        nbr_collab_refused = CollaborationResponse.objects.filter(responder=user,status='refused').count()

        writer.writerow([user.id,user.username,nbr_books_authored,",".join(genres),nbr_books_collab,nbr_collab_accepted,nbr_collab_pending,nbr_collab_refused])

print("✅ Dataset enrichi exporté")
