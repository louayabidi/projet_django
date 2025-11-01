#!/usr/bin/env bash
# build.sh - Script de construction pour Render

set -o errexit

echo "========================================="
echo "    DÉPLOIEMENT DJANGO SUR RENDER"
echo "========================================="

echo "=== 1. Installation des dépendances ==="
pip install -r requirements.txt

echo "=== 2. Collecte des fichiers statiques ==="
python manage.py collectstatic --noinput --clear

echo "=== 3. Application des migrations ==="
python manage.py migrate

echo "=== 4. Vérification du projet ==="
python manage.py check --deploy

echo "========================================="
echo "       ✅ BUILD TERMINÉ AVEC SUCCÈS"
echo "========================================="