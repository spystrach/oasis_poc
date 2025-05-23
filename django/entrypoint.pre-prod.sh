#!/bin/sh

# Attends que la base de donnée soit démarrée
while ! nc -z "$SQL_HOST" "$SQL_PORT"; do
  sleep 0.5
done
echo "Postgres démarré"

# nettoyage de la base de donnée
python manage.py flush --no-input

# application des migrations et création de l'administrateur
python manage.py migrate --no-input
python manage.py createsuperuser --no-input
# collecte des fichiers statiques
python manage.py collectstatic --no-input

# pré-remplissage de la table des fonctions métiers
python manage.py loaddata inventaire/fixtures/inventaire/groupes.json
python manage.py loaddata inventaire/fixtures/inventaire/metiers.json

exec "$@"
