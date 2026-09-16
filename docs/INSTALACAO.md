# Instalação

## Requisitos

- Python 3.12 (ou 3.11)
- Node.js 22+ (para o frontend React em `frontend/`)
- Git
- Docker Desktop (opcional, só para testar a imagem de produção)

## Passo a passo (desenvolvimento local)

1. **Clonar e entrar na pasta**
   ```bash
   git clone <url-do-repo> atletica-crm
   cd atletica-crm
   ```

2. **Ambiente virtual + dependências do backend**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\pip install -r requirements-dev.txt
   # Linux/Mac:
   .venv/bin/pip install -r requirements-dev.txt
   ```
   (`requirements-dev.txt` inclui o `requirements.txt` de produção mais o pytest.)

3. **Arquivo de configuração**
   ```bash
   copy .env.example .env      # Windows
   cp .env.example .env        # Linux/Mac
   ```
   Edite o `.env`:
   - `SECRET_KEY` — gere uma nova:
     ```bash
     python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
     ```
   - `DEBUG=True` (só em desenvolvimento)
   - `DATABASE_URL` vazio → usa SQLite (arquivo `db.sqlite3`)

4. **Banco de dados**
   ```bash
   python manage.py migrate
   ```

5. **Dados iniciais** (perfis de acesso, categorias, identidade visual)
   ```bash
   python manage.py seed_inicial            # só a estrutura
   python manage.py seed_inicial --com-demo  # + dados fictícios para testar
   ```

6. **Usuário administrador**
   ```bash
   python manage.py createsuperuser
   ```
   Depois, associe-o ao perfil Administrador (Django Admin → Membros → o usuário
   → Perfis de acesso → marcar "Administrador"), ou pelo shell:
   ```bash
   python manage.py shell -c "from django.contrib.auth import get_user_model as U; from django.contrib.auth.models import Group as G; u=U().objects.get(username='SEU_USUARIO'); u.groups.add(G.objects.get(name='Administrador')); u.is_staff=True; u.save()"
   ```

7. **Frontend (React + Vite)**
   ```bash
   cd frontend
   npm install
   ```

8. **Rodar** (dois terminais)
   ```bash
   # terminal 1: Django (API + admin + reset de senha + recibo)
   python manage.py runserver 127.0.0.1:8010

   # terminal 2: Vite (frontend, com proxy para o Django)
   cd frontend && npm run dev
   ```
   Abra **http://localhost:5173/** (use `localhost`, não `127.0.0.1`: os
   cookies de sessão e CSRF do Django precisam do mesmo host).
   O admin do Django fica em http://127.0.0.1:8010/admin/ (também acessível pelo Vite).

   Sem o Vite, o Django serve o frontend compilado na raiz:
   ```bash
   cd frontend && npm run build && cd ..
   python manage.py runserver 127.0.0.1:8010   # abra http://127.0.0.1:8010/
   ```

## Testes

```bash
python -m pytest            # backend (API, permissões, auth); usa SQLite em memória
cd frontend && npm run typecheck
```

## Capturas de tela (opcional)

`frontend/scripts/capturas.mjs` tira screenshots do frontend com o Chrome local
(headless), sem digitar senha: a sessão é criada pelo Django.

```bash
# 1) gere um sessionid para o seu usuário
python manage.py shell -c "from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY, get_user_model; from django.contrib.sessions.backends.db import SessionStore; u=get_user_model().objects.get(username='SEU_USUARIO'); s=SessionStore(); s[SESSION_KEY]=str(u.pk); s[BACKEND_SESSION_KEY]='django.contrib.auth.backends.ModelBackend'; s[HASH_SESSION_KEY]=u.get_session_auth_hash(); s.create(); print(s.session_key)"
# 2) com Django (:8010) e Vite (:5173) rodando
cd frontend && SESSAO=<sessionid> SAIDA=../capturas node scripts/capturas.mjs
```

## Problemas comuns

| Sintoma | Causa / solução |
|---|---|
| `redireciona para HTTPS` no runserver | `DEBUG` está `False`. Confirme `DEBUG=True` no `.env`. |
| `SECRET_KEY` warning | Defina `SECRET_KEY` no `.env`. |
| 403 ao logar pelo frontend | Abriu por `127.0.0.1:5173`. Use `http://localhost:5173/`. |
| A raiz responde 503 "Frontend não compilado" | Rode `npm run build` em `frontend/` e reinicie o `runserver` (ou use o Vite). |
| CSS não carrega em produção | Rode `python manage.py collectstatic`. |
| `psycopg` erro ao conectar | Verifique a `DATABASE_URL` (host, senha, porta 5432). |
