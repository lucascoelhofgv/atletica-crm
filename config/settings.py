"""
Configurações do CRM da Atlética FGV Rio.

Lê variáveis sensíveis de um arquivo .env (ver .env.example).
Em desenvolvimento roda com SQLite; em produção basta definir DATABASE_URL
(ex.: a string de conexão do Supabase) que o app passa a usar PostgreSQL.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["*"]),
    CSRF_TRUSTED_ORIGINS=(list, []),
    SECRET_KEY=(str, "dev-inseguro-troque-em-producao"),
)
environ.Env.read_env(BASE_DIR / ".env")

# --------------------------------------------------------------------------- #
# Núcleo
# --------------------------------------------------------------------------- #
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

# No Render, o domínio do serviço é injetado nesta variável automaticamente.
# Assim não é preciso configurar ALLOWED_HOSTS/CSRF na mão.
_render_host = env("RENDER_EXTERNAL_HOSTNAME", default="")
if _render_host:
    if _render_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_render_host)
    origem = f"https://{_render_host}"
    if origem not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origem)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Terceiros
    "simple_history",
    "rest_framework",
    "django_filters",
    # Apps do projeto
    "apps.contas",
    "apps.nucleo",
    "apps.crm",
    "apps.catalogo",
    "apps.fornecedores",
    "apps.vendas",
    "apps.tarefas",
    "apps.eventos",
    "apps.relatorios",
    "apps.api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.nucleo.context_processors.configuracao",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --------------------------------------------------------------------------- #
# Banco de dados
# --------------------------------------------------------------------------- #
_default_sqlite = f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
_database_url = env("DATABASE_URL", default="") or _default_sqlite
DATABASES = {"default": env.db_url_config(_database_url)}
DATABASES["default"].setdefault("CONN_MAX_AGE", 60)

# --------------------------------------------------------------------------- #
# Autenticação
# --------------------------------------------------------------------------- #
AUTH_USER_MODEL = "contas.Membro"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "/login"          # tela do SPA
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login"

# --------------------------------------------------------------------------- #
# Internacionalização — português do Brasil
# --------------------------------------------------------------------------- #
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------- #
# Arquivos estáticos e de mídia
# --------------------------------------------------------------------------- #
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Build do frontend React (Vite). Entra com o prefixo "app": os assets ficam em
# /static/app/assets/... e o index.html é entregue por apps.api.views_spa.
_frontend_dist = BASE_DIR / "frontend" / "dist"
if _frontend_dist.is_dir():
    STATICFILES_DIRS.append(("app", _frontend_dist))

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

# WhiteNoise + assets já hasheados pelo Vite: não falhar por referência
# ausente no manifest e marcar os nomes do Vite como imutáveis (cache longo).
from apps.api.static import eh_imutavel  # noqa: E402  (módulo sem dependências)

WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_IMMUTABLE_FILE_TEST = eh_imutavel

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Limite de upload (seção 16 do escopo): 5 MB por arquivo.
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

# --------------------------------------------------------------------------- #
# Segurança (produção). Ativado automaticamente quando DEBUG = False.
# --------------------------------------------------------------------------- #
if not DEBUG:
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
    # O health check do Render chega por HTTP e não pode receber 301.
    SECURE_REDIRECT_EXEMPT = [r"^api/saude/$"]
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # COOKIES_SECURE=False só para testar a imagem Docker em http://localhost.
    SESSION_COOKIE_SECURE = env.bool("COOKIES_SECURE", default=True)
    CSRF_COOKIE_SECURE = env.bool("COOKIES_SECURE", default=True)
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # o frontend lê o cookie para mandar X-CSRFToken
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_AGE = 60 * 60 * 12  # 12 horas
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# --------------------------------------------------------------------------- #
# API (Django REST Framework) consumida pelo frontend React em frontend/
# --------------------------------------------------------------------------- #
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "apps.api.pagination.PaginacaoPadrao",
    "PAGE_SIZE": 30,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "SEARCH_PARAM": "q",
    "ORDERING_PARAM": "ordenar",
    "EXCEPTION_HANDLER": "apps.api.exceptions.tratar",
    "DEFAULT_RENDERER_CLASSES": (
        ["rest_framework.renderers.JSONRenderer"]
        + (["rest_framework.renderers.BrowsableAPIRenderer"] if DEBUG else [])
    ),
    "COERCE_DECIMAL_TO_STRING": False,
    "DATE_FORMAT": "%Y-%m-%d",
    "DATETIME_FORMAT": "iso-8601",
}

# --------------------------------------------------------------------------- #
# E-mail (recuperação de senha). Em dev imprime no console.
# --------------------------------------------------------------------------- #
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = env(
        "EMAIL_BACKEND",
        default="django.core.mail.backends.console.EmailBackend",
    )
    EMAIL_HOST = env("EMAIL_HOST", default="")
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)

DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL", default="CRM Atlética <nao-responder@atletica.local>"
)

# --------------------------------------------------------------------------- #
# Integração com Google Sheets (fase 2 — só é usada se configurada)
# --------------------------------------------------------------------------- #
GOOGLE_SERVICE_ACCOUNT_FILE = env(
    "GOOGLE_SERVICE_ACCOUNT_FILE",
    default=str(BASE_DIR / "google-service-account.json"),
)
GOOGLE_SHEETS_SPREADSHEET_ID = env("GOOGLE_SHEETS_SPREADSHEET_ID", default="")

# --------------------------------------------------------------------------- #
# Logging simples para console (visível no Render)
# --------------------------------------------------------------------------- #
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
