#!/bin/sh

# Attends que la base de donnée soit démarrée
while ! nc -z "$SQL_HOST" "$SQL_PORT"; do
  sleep 0.5
done
echo "Postgres démarré"

# application des migrations
python manage.py migrate --no-input
# collecte des fichiers statiques
python manage.py collectstatic --no-input

exec "$@"
