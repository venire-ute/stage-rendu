#!/bin/sh
# Attente Postgres
echo " Attente PostgreSQL..."
while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 1
done
echo " PostgreSQL prêt"
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Création de l'utilisateur superutilisateur
python manage.py  create_superuser

exec "$@" # Exécution du serveur
