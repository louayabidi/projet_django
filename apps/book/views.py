from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from .models import Book
from .forms import BookForm
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from io import BytesIO
from datetime import datetime
import requests
from django.core.files.base import ContentFile
from .utils import (
    sequence_similarity, tfidf_similarity, 
    ngram_similarity, embedding_similarity, clean_text, check_web_plagiarism
)
from django.utils.html import strip_tags
import re
import os

# .
# Test route
@login_required
def test_view(request):
    return HttpResponse("La route /books/test/ fonctionne correctement ✅")

# Liste des livres
@login_required
def book_list(request):
    """
    Admin: voit tous les livres
    Artiste: voit seulement ses livres
    """
    if request.user.is_staff:  # admin
        books = Book.objects.all()
    else:  # artiste
        books = Book.objects.filter(author=request.user)
    return render(request, 'book/book_list.html', {'books': books})


def read_book_text(book):
        """Lit le texte propre (fichier .txt ou contenu HTML nettoyé)"""
        # 1. Essayer le fichier .txt
        if book.file:
            try:
                with open(book.file.path, 'r', encoding='utf-8') as f:
                    return clean_text(f.read())
            except:
                pass

        # 2. Sinon, fallback sur book.content (HTML)
        return clean_text(book.content)

def check_plagiarism_on_save(book, request):
    test_text = read_book_text(book)
    if len(test_text) < 100:
        messages.info(request, "Contenu trop court pour analyse.")
        return

    # 1. Plagiat dans la DB
    existing_books = Book.objects.exclude(id=book.id).filter(author=book.author)
    db_max_sim = 0
    similar_title = ""
    high_db_plagiarism = False

    for other in existing_books:
        other_text = read_book_text(other)
        if len(other_text) < 50:
            continue
        scores = [
            sequence_similarity(test_text, other_text),
            tfidf_similarity(test_text, other_text),
            embedding_similarity(test_text, other_text),
            ngram_similarity(test_text, other_text, n=5)
        ]
        avg = sum(scores) / len(scores)
        if avg > db_max_sim:
            db_max_sim = avg
            similar_title = other.title
        if avg > 0.75:
            high_db_plagiarism = True
            break  # On arrête dès qu'on a un plagiat fort

    # 2. Plagiat sur le web
    web_matches = []
    try:
        web_matches = check_web_plagiarism(test_text)
    except Exception as e:
        print(f"Erreur web: {e}")

    # 3. UN SEUL MESSAGE FINAL
    if high_db_plagiarism:
        msg = f"Plagiat DB détecté avec « {similar_title} » ({round(db_max_sim*100,1)}%)"
        if web_matches:
            msg += f" | Web: {len(web_matches)} match(s)"
        messages.warning(request, msg)
    elif web_matches:
        msg = f"Plagiat web détecté ({len(web_matches)} phrase(s)) | DB: {round(db_max_sim*100,1)}%"
        messages.warning(request, msg)
    else:
        messages.success(request, f"Sauvegardé ! DB: {round(db_max_sim*100,1)}% | Web: OK")
# Ajouter un livre
@login_required
def book_create(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.author = request.user
            book.save()

            # Créer un fichier .txt à partir du contenu éditeur si vide
            if not book.file and book.content:
                content_text = strip_tags(book.content)
                if content_text.strip():
                    filename = f"{book.title.replace(' ', '_')}.txt"
                    book.file.save(filename, ContentFile(content_text.encode('utf-8')))
                    book.save()

            # Détection de plagiat
            check_plagiarism_on_save(book, request)
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'book/book_form.html', {'form': form})

    
# Modifier un livre
@login_required
def book_update(request, id):
    book = get_object_or_404(Book, id=id)
    if not request.user.is_staff and book.author != request.user:
        return HttpResponse("Accès refusé", status=403)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)  # Ajout de request.FILES
        if form.is_valid():
            form.save()
            messages.success(request, "Livre modifié avec succès !")
            return redirect('book_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'book/book_form.html', {'form': form})

# Supprimer un livre
@login_required
def book_delete(request, id):
    book = get_object_or_404(Book, id=id)
    if not request.user.is_staff and book.author != request.user:
        return HttpResponse("Accès refusé", status=403)
    if request.method == 'POST':
        book.delete()
        messages.success(request, "Livre supprimé avec succès !")
        return redirect('book_list')
    return render(request, 'book/book_confirm_delete.html', {'book': book})

# Télécharger un livre en PDF
@login_required
def book_download_pdf(request, id):
    book = get_object_or_404(Book, id=id)
    if not request.user.is_staff and book.author != request.user:
        messages.error(request, "Vous n'avez pas la permission de télécharger ce livre.")
        return redirect('book_list')
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Heading1'], fontSize=28, textColor=colors.HexColor('#667eea'),
        spaceAfter=30, alignment=TA_CENTER, fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle', parent=styles['Heading2'], fontSize=16, textColor=colors.HexColor('#764ba2'),
        spaceAfter=12, spaceBefore=20, fontName='Helvetica-Bold'
    )
    normal_style = ParagraphStyle(
        'CustomNormal', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#2d3142'),
        alignment=TA_JUSTIFY, spaceAfter=10, leading=16
    )
    meta_style = ParagraphStyle(
        'MetaStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#6c757d'),
        alignment=TA_LEFT, spaceAfter=6
    )
    
    title = Paragraph(f"📚 {book.title}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2 * inch))
    
    data = [
        ['Auteur:', book.author.get_full_name() or book.author.username],
        ['Genre:', book.genre],
        ['Statut:', dict(book._meta.get_field('status').choices).get(book.status, book.status)],
        ['Créé le:', book.created_at.strftime('%d/%m/%Y à %H:%M')],
        ['Modifié le:', book.updated_at.strftime('%d/%m/%Y à %H:%M')],
    ]
    
    table = Table(data, colWidths=[2*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9ff')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#667eea')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2d3142')),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('PADDING', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e6e7ee')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#fafbff')]),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.4 * inch))
    
    synopsis_title = Paragraph("📖 Synopsis", subtitle_style)
    elements.append(synopsis_title)
    synopsis_text = book.synopsis.replace('\n', '<br/>')
    synopsis = Paragraph(synopsis_text, normal_style)
    elements.append(synopsis)
    elements.append(Spacer(1, 0.5 * inch))
    
    footer_text = f"<i>Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</i>"
    footer = Paragraph(footer_text, meta_style)
    elements.append(footer)
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="livre_{book.id}_{book.title[:30]}.pdf"'
    response.write(pdf)
    return response

# Télécharger des livres exemples
@login_required
def download_example_books(request):
    books_data = [
        {
            'url': 'https://www.gutenberg.org/files/1342/1342-0.txt',
            'title': 'Pride and Prejudice',
            'genre': 'Roman',
            'status': 'termine'
        },
        {
            'url': 'https://www.gutenberg.org/files/84/84-0.txt',
            'title': 'Frankenstein',
            'genre': 'Science-fiction',
            'status': 'termine'
        },
        {
            'url': 'https://www.gutenberg.org/files/11/11-0.txt',
            'title': 'Alice in Wonderland (pour test)',
            'genre': 'Fantaisie',
            'status': 'en_cours'
        }
    ]

    for data in books_data:
        response = requests.get(data['url'])
        if response.status_code == 200:
            text = response.text
            book = Book(
                title=data['title'],
                synopsis=text[:500],
                genre=data['genre'],
                status=data['status'],
                author=request.user
            )
            book.save()
            book.file.save(f"{data['title']}.txt", ContentFile(text.encode('utf-8')))
            book.save()

    messages.success(request, "3 livres exemples téléchargés et ajoutés à la DB (2 pour DB, 1 pour test).")
    return redirect('book_list')

# Test de plagiat
@login_required
def plagiarism_test(request):
    books = Book.objects.all()
    if books.count() < 2:
        return JsonResponse({"error": "Ajoutez au moins 2 livres pour tester."})

    test_book = books.last()
    test_text = read_book_text(test_book)
    other_books = books.exclude(id=test_book.id)
    results = []

    for book in other_books:
        book_text = read_book_text(book)
        results.append({
            "book_id": book.id,
            "book_title": book.title,
            "sequence_similarity": round(sequence_similarity(test_text, book_text), 2),
            "tfidf_similarity": round(tfidf_similarity(test_text, book_text), 2),
            "embedding_similarity": round(embedding_similarity(test_text, book_text), 2),
            "ngram_similarity": round(ngram_similarity(test_text, book_text), 2)
        })

    return JsonResponse({
        "test_book": {"id": test_book.id, "title": test_book.title},
        "similarities": results
    })


def read_book_content(file_field):
    
    if not file_field:
        return "Aucun fichier disponible."

    file_path = file_field.path
    if not os.path.exists(file_path):
        return "Fichier introuvable."

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Erreur lors de la lecture du fichier : {e}"

# Éditeur de texte pour le livre
# views.py → book_editor

@login_required
def book_editor(request, id):
    book = get_object_or_404(Book, id=id)
    if not request.user.is_staff and book.author != request.user:
        return redirect('book_list')

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        book.content = content
        book.save()

        # Générer fichier .txt
        if content:
            filename = f"{book.title.replace(' ', '_')}.txt"
            if book.file:
                book.file.delete(save=False)
            book.file.save(filename, ContentFile(content.encode('utf-8')), save=False)
        book.save()

        # Vérification plagiat
        check_plagiarism_on_save(book, request)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            storage = messages.get_messages(request)
            message_list = [{'text': str(m), 'tags': m.tags} for m in storage]
            return JsonResponse({'success': True, 'messages': message_list})

        return redirect('book_list')

    return render(request, 'book/book_editor.html', {'book': book})


def check_plagiarism_on_save(book, request):
    test_text = read_book_text(book)
    if len(test_text) < 100:
        messages.info(request, "Contenu trop court pour analyse.")
        return

    # 1. Plagiat dans la DB
    existing_books = Book.objects.exclude(id=book.id).filter(author=book.author)
    db_max_sim = 0
    similar_title = ""

    for other in existing_books:
        other_text = read_book_text(other)
        if len(other_text) < 50:
            continue
        scores = [
            sequence_similarity(test_text, other_text),
            tfidf_similarity(test_text, other_text),
            embedding_similarity(test_text, other_text),
            ngram_similarity(test_text, other_text, n=5)
        ]
        avg = sum(scores) / len(scores)
        if avg > db_max_sim:
            db_max_sim = avg
            similar_title = other.title

    # 2. Plagiat sur le web
    web_matches = []
    try:
        web_matches = check_web_plagiarism(test_text)
    except:
        pass  # En cas d'erreur réseau

    # 3. Messages
    if db_max_sim > 0.75:
        messages.warning(request, f"Plagiat DB détecté avec « {similar_title} » ({round(db_max_sim*100,1)}%)")
    elif db_max_sim > 0.5:
        messages.info(request, f"Similarité DB : {round(db_max_sim*100,1)}% avec « {similar_title} »")

    if web_matches:
        for match in web_matches[:2]:  # Max 2 alertes
            messages.warning(request, f"Plagiat web détecté : « {match['sentence'][:60]}... » → {match['url']} ({match['similarity']}%)")
    else:
        messages.success(request, f"Sauvegardé ! DB: {round(db_max_sim*100,1)}% | Web: OK")