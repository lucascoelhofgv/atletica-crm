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

1. Em https://console.cloud.google.com crie um projeto (ex.: "CRM Atlética").
2. **APIs & Services → Enabled APIs & services → + Enable APIs and services** →
   ative **Google Sheets API** e **Google Drive API** (uma de cada vez).
3. **APIs & Services → Credentials → Create credentials → Service account**.
   Dê um nome (ex.: `crm-sheets`), crie. Abra a service account criada, aba
   **Keys → Add key → Create new key → JSON**. Baixa um arquivo `.json`.
4. Crie uma planilha nova no Google Sheets (ex.: "CRM Atlética — Dados").
   **Compartilhe** essa planilha com o e-mail da service account (algo como
   `crm-sheets@crm-atletica.iam.gserviceaccount.com`, está dentro do JSON no
   campo `client_email`), com permissão de **Editor**.
5. Configure o ambiente:
   - `GOOGLE_SHEETS_SPREADSHEET_ID` = o trecho entre `/d/` e `/edit` da URL da
     planilha.
   - **Credenciais** — escolha UMA forma:
     - **Render / produção (recomendado):** `GOOGLE_SERVICE_ACCOUNT_JSON` =
       o conteúdo **inteiro** do arquivo `.json`, colado como valor da variável
       (o Render aceita várias linhas no campo de valor).
     - **Dev local:** salve o `.json` como `google-service-account.json` na raiz
       do projeto (já está no `.gitignore`) ou aponte `GOOGLE_SERVICE_ACCOUNT_FILE`
       para o caminho dele.
6. No Render: **Environment → Add Environment Variable**, adicione as duas acima
   e salve (o Render redeploya sozinho).
7. Sincronize:
   - manualmente: menu **Google Sheets** no sistema → "Sincronizar dados gerais"
     e "Sincronizar aba Festas";
   - agendado (opcional): `python manage.py exportar_sheets` e
     `python manage.py exportar_festas`.
