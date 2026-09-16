#!/usr/bin/env sh
# Start da imagem Docker (Render free não tem fase de "release", então as
# migrações rodam aqui). Todos os comandos são idempotentes.
set -e

python manage.py migrate --noinput
python manage.py seed_inicial
python manage.py bootstrap_admin

exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --threads 4 \
  --timeout 120 \
  --log-file -
