# Publicação (custo zero)

Arquitetura: **Render** (aplicação web, plano free) + **Supabase** (PostgreSQL,
plano free). O plano free do Render "dorme" após ~15 min sem acesso e leva
~50 s para acordar — aceitável para uso interno.

## 1. Banco de dados no Supabase

1. Crie uma conta em https://supabase.com e um novo projeto (região South America).
2. Em **Project Settings → Database → Connection string → URI**, copie a string
   (formato `postgresql://postgres:SENHA@HOST:5432/postgres`).
   Use a porta **5432** (conexão direta) ou o **Session pooler** (porta 6543)
   para plano free.
3. Guarde essa string — será a `DATABASE_URL` no Render.

> O projeto Supabase free pausa após ~1 semana sem uso. Com uso regular da
> Atlética isso não ocorre; se necessário, agende um "ping" (ver seção 4).

## 2. Aplicação no Render

1. Suba o código para um repositório no GitHub.
2. Em https://render.com → **New → Blueprint**, conecte o repositório. O Render
   lê o `render.yaml` e cria o serviço `crm-atletica`.
3. Configure as variáveis de ambiente (algumas já vêm do `render.yaml`):

   | Variável | Valor |
   |---|---|
   | `SECRET_KEY` | gerado automaticamente |
   | `DEBUG` | `False` |
   | `ALLOWED_HOSTS` | `.onrender.com` (e depois seu domínio) |
   | `CSRF_TRUSTED_ORIGINS` | `https://SEU-APP.onrender.com` |
   | `DATABASE_URL` | a string do Supabase (passo 1) |
   | `EMAIL_*` | opcional, para recuperação de senha por e-mail |

4. O **Build Command** (`./build.sh`) roda `collectstatic` e `migrate`
   automaticamente a cada deploy.
5. Após o primeiro deploy, abra o **Shell** do Render e rode:
   ```bash
   python manage.py seed_inicial
   python manage.py createsuperuser
   python manage.py shell -c "from django.contrib.auth import get_user_model as U; from django.contrib.auth.models import Group as G; u=U().objects.get(username='SEU_USUARIO'); u.groups.add(G.objects.get(name='Administrador')); u.is_staff=True; u.save()"
   ```

## 3. Arquivos enviados (logos, comprovantes)

O disco do Render free é efêmero. Para uploads persistentes, configure um
storage S3-compatível (Supabase Storage ou Cloudflare R2, ambos com free tier)
via `django-storages`. Enquanto o volume for pequeno, o disco do Render resolve,
mas os arquivos somem a cada redeploy — trate como fase de ajuste.

## 4. Manter o serviço acordado (opcional)

GitHub Actions gratuito, arquivo `.github/workflows/ping.yml`:
```yaml
name: ping
on:
  schedule: [{cron: "*/10 * * * *"}]
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - run: curl -sS https://SEU-APP.onrender.com/ > /dev/null
```

---

# Integração Google Sheets

1. Em https://console.cloud.google.com crie um projeto.
2. **APIs & Services → Enable APIs** → ative **Google Sheets API** e
   **Google Drive API**.
3. **Credentials → Create credentials → Service account**. Crie e, na aba
   **Keys**, gere uma chave **JSON**. Baixe o arquivo.
4. Crie a planilha de destino no Google Sheets. **Compartilhe** a planilha com o
   e-mail da service account (algo como `...@...iam.gserviceaccount.com`), como
   **Editor**.
5. Configure o ambiente:
   - `GOOGLE_SERVICE_ACCOUNT_FILE` = caminho do JSON (no Render, use um
     *Secret File* e aponte para `/etc/secrets/google.json`).
   - `GOOGLE_SHEETS_SPREADSHEET_ID` = o trecho entre `/d/` e `/edit` da URL da
     planilha.
6. Sincronize:
   - manualmente: menu **Google Sheets** no sistema → "Sincronizar agora";
   - por linha de comando / agendado: `python manage.py exportar_sheets`.
