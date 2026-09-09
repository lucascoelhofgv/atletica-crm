#!/usr/bin/env bash
# Script de build para o Render (Build Command).
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Estrutura básica (perfis de acesso, categorias, configuração). Idempotente.
python manage.py seed_inicial

# Cria/atualiza o admin SE as variáveis ADMIN_USERNAME/ADMIN_PASSWORD existirem.
# Sem elas, não faz nada. Serve para plataformas sem shell (Render free).
python manage.py bootstrap_admin
