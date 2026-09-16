#!/usr/bin/env bash
# Build para ambientes SEM Docker (runtime Python nativo do Render, por exemplo).
# O caminho oficial de deploy é o Dockerfile; este script continua funcionando
# desde que o ambiente tenha Node para compilar o frontend.
set -o errexit

pip install -r requirements.txt

if command -v npm >/dev/null 2>&1 && [ -d frontend ]; then
  (cd frontend && npm ci && npm run build)
else
  echo "AVISO: npm não encontrado; o frontend React não será compilado."
fi

python manage.py collectstatic --no-input
python manage.py migrate

# Estrutura básica (perfis de acesso, categorias, configuração). Idempotente.
python manage.py seed_inicial

# Cria/atualiza o admin SE as variáveis ADMIN_USERNAME/ADMIN_PASSWORD existirem.
# Sem elas, não faz nada. Serve para plataformas sem shell (Render free).
python manage.py bootstrap_admin
