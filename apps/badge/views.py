from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Badge, UserBadge
from .forms import BadgeForm
from .services import BadgeService

@login_required
def badge_list(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'role') or request.user.role != 'admin':
        messages.error(request, "Accès refusé.")
        return redirect('badge:your_badges')

    badges = Badge.objects.all().order_by('-date_creation')  # Tri récent

    return render(request, 'badge/badge_list.html', {
        'badges': badges,
        'title': 'Gestion des Badges',
        'segment': 'badge_list'  # Pour activer le lien dans la sidebar
    })

@login_required
def badge_create(request):
    if not (hasattr(request.user, 'role') and request.user.role == 'admin'):
        messages.error(request, "Vous n'avez pas la permission de créer des badges.")
        return redirect('badge:badge_list')
    
    if request.method == 'POST':
        form = BadgeForm(request.POST, request.FILES)
        if form.is_valid():
            badge = form.save()
            
            # DEBUG : affiche l'objet badge
            print("BADGE CRÉÉ → ID:", badge.id, "| NOM:", badge.nom, "| IMAGE:", badge.image)

            # Initialiser pour tous les utilisateurs
            from django.contrib.auth import get_user_model
            User = get_user_model()
            for user in User.objects.all():
                UserBadge.objects.get_or_create(user=user, badge=badge)
            
            messages.success(request, f'Le badge "{badge.nom}" a été créé avec succès!')
            return redirect('badge:badge_list')
    else:
        form = BadgeForm()
    
    return render(request, 'badge/badge_form.html', {
        'form': form,
        'title': 'Créer un badge',
        'segment': 'badge_create'
    })

@login_required
def badge_update(request, pk):
    # Seul l'admin peut modifier des badges
    if not (hasattr(request.user, 'role') and request.user.role == 'admin'):
        messages.error(request, "Vous n'avez pas la permission de modifier des badges.")
        return redirect('badge:badge_list')
    
    badge = get_object_or_404(Badge, pk=pk)
    
    if request.method == 'POST':
        form = BadgeForm(request.POST, request.FILES, instance=badge)
        if form.is_valid():
            badge = form.save()
            messages.success(request, f'Le badge "{badge.nom}" a été modifié avec succès!')
            return redirect('badge:badge_list')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = BadgeForm(instance=badge)
    
        return render(request, 'badge/badge_form.html', {
        'form': form,
        'title': 'Modifier le badge',
        'badge': badge,
        'segment': 'badge_update'
    })
@login_required
def badge_delete(request, pk):
    # Seul l'admin peut supprimer des badges
    if not (hasattr(request.user, 'role') and request.user.role == 'admin'):
        messages.error(request, "Vous n'avez pas la permission de supprimer des badges.")
        return redirect('badge:badge_list')
    
    badge = get_object_or_404(Badge, pk=pk)
    
    if request.method == 'POST':
        nom = badge.nom
        badge.delete()
        messages.success(request, f'Le badge "{nom}" a été supprimé avec succès!')
        return redirect('badge:badge_list')
    
    return render(request, 'badge/badge_confirm_delete.html', {'badge': badge})

@login_required
def badge_detail(request, pk):
    """Détails d'un badge (admin seulement)"""
    if not (hasattr(request.user, 'role') and request.user.role == 'admin'):
        messages.error(request, "Vous n'avez pas la permission de voir les détails des badges.")
        return redirect('badge:your_badges')
    
    badge = get_object_or_404(Badge, pk=pk)
    
    # Statistiques du badge
    total_users = UserBadge.objects.filter(badge=badge).count()
    unlocked_users = UserBadge.objects.filter(badge=badge, unlocked=True).count()
    
    context = {
        'badge': badge,
        'total_users': total_users,
        'unlocked_users': unlocked_users,
        'locked_users': total_users - unlocked_users,
    }
    
    return render(request, 'badge/badge_detail.html', context)

@login_required
def your_badges(request):
    """Endpoint pour afficher les badges de l'utilisateur connecté"""
    # Initialiser les badges si nécessaire
    BadgeService.initialize_user_badges(request.user)
    
    # Vérifier et débloquer les badges
    newly_unlocked = BadgeService.check_and_unlock_badges(request.user)
    
    if newly_unlocked:
        messages.success(request, f'Félicitations! Vous avez débloqué {len(newly_unlocked)} nouveau(x) badge(s)!')
    
    # Récupérer tous les badges de l'utilisateur
    user_badges = UserBadge.objects.filter(user=request.user).select_related('badge')
    
    unlocked_badges = user_badges.filter(unlocked=True)
    locked_badges = user_badges.filter(unlocked=False)
    
    context = {
        'unlocked_badges': unlocked_badges,
        'locked_badges': locked_badges,
        'total_badges': user_badges.count(),
        'unlocked_count': unlocked_badges.count(),
    }
    
    return render(request, 'badge/your_badges.html', context)