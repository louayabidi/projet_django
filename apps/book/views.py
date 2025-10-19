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
from .utils import sequence_similarity, tfidf_similarity, embedding_similarity, ngram_similarity, read_book_file

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

# Ajouter un livre
@login_required
def book_create(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the book
            book = form.save(commit=False)
            book.author = request.user
            book.save()

            # Perform plagiarism check
            existing_books = Book.objects.exclude(id=book.id)
            if existing_books.count() == 0:
                messages.success(request, "Livre ajouté avec succès ! Aucun autre livre dans la base pour comparer.")
            else:
                try:
                    test_text = read_book_file(book)
                    high_similarity_found = False
                    max_similarity = 0
                    similar_book_title = ""

                    for existing_book in existing_books:
                        existing_text = read_book_file(existing_book)
                        scores = {
                            "sequence": sequence_similarity(test_text, existing_text),
                            "tfidf": tfidf_similarity(test_text, existing_text),
                            "embedding": embedding_similarity(test_text, existing_text),
                            "ngram": ngram_similarity(test_text, existing_text)
                        }
                        # Calculate average similarity
                        avg_similarity = sum(scores.values()) / len(scores)
                        if avg_similarity > max_similarity:
                            max_similarity = avg_similarity
                            similar_book_title = existing_book.title

                        # Flag if any similarity score exceeds threshold
                        if any(score > 0.5 for score in scores.values()):
                            high_similarity_found = True
                            similar_book_title = existing_book.title
                            break  # Stop checking further books if high similarity is found

                    if high_similarity_found:
                        messages.warning(
                            request,
                            f"Attention : Potentiel plagiat détecté avec '{similar_book_title}'. "
                            f"Score de similarité moyen : {round(max_similarity * 100, 2)}%. "
                            "Veuillez vérifier le contenu du livre."
                        )
                    else:
                        messages.success(
                            request,
                            f"Livre ajouté avec succès ! Aucun plagiat détecté (similarité max : {round(max_similarity * 100, 2)}%)."
                        )

                except Exception as e:
                    messages.error(
                        request,
                        f"Erreur lors de la vérification du plagiat : {str(e)}. Livre ajouté, mais vérifiez manuellement."
                    )

            return redirect('book_list')
        else:
            messages.error(request, "Erreur lors de l'ajout du livre. Vérifiez les champs.")
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
    test_text = read_book_file(test_book)
    other_books = books.exclude(id=test_book.id)
    results = []

    for book in other_books:
        book_text = read_book_file(book)
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