# syntax=docker/dockerfile:1
# Imagem única para o Render: o estágio 1 compila o frontend (Vite) e o
# estágio 2 roda o Django, que serve a API e o SPA (via WhiteNoise).

# --- Estágio 1: build do frontend ------------------------------------------
FROM node:22-alpine AS web
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Estágio 2: Django + assets --------------------------------------------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000
WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .
COPY --from=web /src/frontend/dist ./frontend/dist

# Arquivos criados no Windows podem vir com CRLF; o shell não aceita.
RUN sed -i 's/\r$//' docker/entrypoint.sh build.sh && chmod +x docker/entrypoint.sh

# collectstatic não toca no banco: pode rodar no build (imagem sai pronta).
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["docker/entrypoint.sh"]
