"""Roteamento principal do CRM da Atlética Gorilada FGV.

O frontend React (SPA) atende a raiz. Continuam server-rendered apenas:
``/admin/`` (Django Admin), ``/api/`` (DRF), ``/conta/senha/...`` (reset de
senha por e-mail), ``/pedidos/<id>/recibo/`` (recibo para impressão) e os
arquivos de ``/static/`` e ``/media/``.
"""

from django.conf import settings
from django.contrib import admin
from django.http import HttpResponsePermanentRedirect
from django.urls import include, path, re_path
from django.views.static import serve

from apps.api.views_spa import spa_index

admin.site.site_header = "CRM Atlética — Administração"
admin.site.site_title = "CRM Atlética"
admin.site.index_title = "Painel administrativo"


def redirecionar_app(request, resto=""):
    """Links antigos do período de migração (/app/...) caem na raiz."""
    destino = "/" + (resto or "")
    if request.META.get("QUERY_STRING"):
        destino += "?" + request.META["QUERY_STRING"]
    return HttpResponsePermanentRedirect(destino)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.api.urls")),
    path("conta/", include("apps.contas.urls")),
    path("pedidos/", include("apps.vendas.urls")),
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    re_path(r"^app(?:/(?P<resto>.*))?$", redirecionar_app),
    # Tudo o mais é rota do SPA (o index.html decide o que mostrar).
    re_path(r"^(?!admin/|api/|static/|media/|conta/).*$", spa_index, name="spa"),
]
