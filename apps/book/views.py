from django.shortcuts import render, get_object_or_404, redirect
from .models import Book
from .forms import BookForm
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages  # pour les messages flash
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime

# ---------------------------------------
# Test route
# ---------------------------------------
def test_view(request):
    return HttpResponse("La route /books/test/ fonctionne correctement ✅")


# ---------------------------------------
# Liste des livres
# ---------------------------------------
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


# ---------------------------------------
# Ajouter un livre
# ---------------------------------------
@login_required
def book_create(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save(commit=False)
            book.author = request.user  # assigner automatiquement l'artiste
            book.save()
            messages.success(request, "Livre ajouté avec succès !")
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'book/book_form.html', {'form': form})


# ---------------------------------------
# Modifier un livre
# ---------------------------------------
@login_required
def book_update(request, id):
    book = get_object_or_404(Book, id=id)

    # Vérifier que l'utilisateur a le droit
    if not request.user.is_staff and book.author != request.user:
        return HttpResponse("Accès refusé", status=403)

    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, "Livre modifié avec succès !")
            return redirect('book_list')
    else:
        form = BookForm(instance=book)

    return render(request, 'book/book_form.html', {'form': form})


# ---------------------------------------
# Supprimer un livre
# ---------------------------------------
@login_required
def book_delete(request, id):
    book = get_object_or_404(Book, id=id)

    # Vérifier que l'utilisateur a le droit
    if not request.user.is_staff and book.author != request.user:
        return HttpResponse("Accès refusé", status=403)

    if request.method == 'POST':
        book.delete()
        messages.success(request, "Livre supprimé avec succès !")
        return redirect('book_list')

    return render(request, 'book/book_confirm_delete.html', {'book': book})


# ---------------------------------------
# Télécharger un livre en PDF
# ---------------------------------------
@login_required
def book_download_pdf(request, id):
    """
    Génère et télécharge un PDF avec les informations du livre
    """
    book = get_object_or_404(Book, id=id)
    
    # Vérifier que l'utilisateur a le droit (admin ou auteur du livre)
    if not request.user.is_staff and book.author != request.user:
        messages.error(request, "Vous n'avez pas la permission de télécharger ce livre.")
        return redirect('book_list')
    
    # Créer le PDF en mémoire
    buffer = BytesIO()
    
    # Créer le document PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container pour les éléments du PDF
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Style personnalisé pour le titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Style pour les sous-titres
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#764ba2'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    # Style pour le texte normal
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#2d3142'),
        alignment=TA_JUSTIFY,
        spaceAfter=10,
        leading=16
    )
    
    # Style pour les métadonnées
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#6c757d'),
        alignment=TA_LEFT,
        spaceAfter=6
    )
    
    # Ajouter le titre du livre
    title = Paragraph(f"📚 {book.title}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2 * inch))
    
    # Créer une table pour les informations
    data = [
        ['Auteur:', book.author.get_full_name() or book.author.username],
        ['Genre:', book.genre],
        ['Statut:', dict(book._meta.get_field('status').choices).get(book.status, book.status)],
        ['Créé le:', book.created_at.strftime('%d/%m/%Y à %H:%M')],
        ['Modifié le:', book.updated_at.strftime('%d/%m/%Y à %H:%M')],
    ]
    
    # Style de la table
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
    
    # Ajouter le synopsis
    synopsis_title = Paragraph("📖 Synopsis", subtitle_style)
    elements.append(synopsis_title)
    
    # Nettoyer le synopsis pour le PDF
    synopsis_text = book.synopsis.replace('\n', '<br/>')
    synopsis = Paragraph(synopsis_text, normal_style)
    elements.append(synopsis)
    
    elements.append(Spacer(1, 0.5 * inch))
    
    # Ajouter un pied de page avec la date de génération
    footer_text = f"<i>Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</i>"
    footer = Paragraph(footer_text, meta_style)
    elements.append(footer)
    
    # Construire le PDF
    doc.build(elements)
    
    # Récupérer le contenu du buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Créer la réponse HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="livre_{book.id}_{book.title[:30]}.pdf"'
    response.write(pdf)
    
    return response
