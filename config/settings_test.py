"""Settings usados pelo pytest: sempre SQLite em memória (nunca o banco do
.env) e hasher de senha rápido."""

from .settings import *  # noqa: F401,F403

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
DEBUG = False
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# WhiteNoise sem STATIC_ROOT coletado nos testes
WHITENOISE_AUTOREFRESH = True
