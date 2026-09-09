# Instalação

## Requisitos

- Python 3.12 (ou 3.11)
- Git

## Passo a passo (desenvolvimento local)

1. **Clonar e entrar na pasta**
   ```bash
   git clone <url-do-repo> atletica-crm
   cd atletica-crm
   ```

2. **Ambiente virtual + dependências**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\pip install -r requirements.txt
   # Linux/Mac:
   .venv/bin/pip install -r requirements.txt
   ```

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

7. **Rodar**
   ```bash
   python manage.py runserver
   ```
   Acesse http://127.0.0.1:8000

## Problemas comuns

| Sintoma | Causa / solução |
|---|---|
| `redireciona para HTTPS` no runserver | `DEBUG` está `False`. Confirme `DEBUG=True` no `.env`. |
| `SECRET_KEY` warning | Defina `SECRET_KEY` no `.env`. |
| CSS não carrega em produção | Rode `python manage.py collectstatic`. |
| `psycopg` erro ao conectar | Verifique a `DATABASE_URL` (host, senha, porta 5432). |
