"""Entrega o ``index.html`` do frontend (Vite) para as rotas do SPA (raiz).

O build fica em ``frontend/dist`` e entra em ``STATICFILES_DIRS`` com o
prefixo ``app``; os assets (``/static/app/assets/...``) são servidos pelo
WhiteNoise. O ``index.html`` em si é lido daqui (nunca cacheado no navegador,
para um deploy novo trocar os assets na hora).

Não usamos ``staticfiles.finders.find``: no Windows ele monta o prefixo com
``os.sep`` e não casa com ``app/index.html``.
"""

from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie

MENSAGEM_SEM_BUILD = (
    "Frontend não compilado.\n\n"
    "Em desenvolvimento, use o Vite: `cd frontend && npm run dev` e abra "
    "http://localhost:5173/.\n"
    "Para servir pelo Django, rode `npm run build` em frontend/ antes "
    "(e reinicie o servidor).\n"
)


def _caminho_index():
    for entrada in settings.STATICFILES_DIRS:
        if isinstance(entrada, (tuple, list)) and entrada[0] == "app":
            caminho = Path(entrada[1]) / "index.html"
            if caminho.is_file():
                return caminho
    caminho = Path(settings.STATIC_ROOT) / "app" / "index.html"
    return caminho if caminho.is_file() else None


def _ler_index():
    caminho = _caminho_index()
    if caminho is None:
        return None
    return caminho.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _index_em_cache():
    return _ler_index()


@ensure_csrf_cookie
def spa_index(request, *args, **kwargs):
    html = _ler_index() if settings.DEBUG else _index_em_cache()
    if html is None:
        return HttpResponse(
            MENSAGEM_SEM_BUILD, status=503, content_type="text/plain; charset=utf-8"
        )
    resposta = HttpResponse(html)
    resposta["Cache-Control"] = "no-store"
    return resposta
