"""Roteamento principal do CRM da Atlética FGV Rio."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "CRM Atlética — Administração"
admin.site.site_title = "CRM Atlética"
admin.site.index_title = "Painel administrativo"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("conta/", include("apps.contas.urls")),
    path("", include("apps.nucleo.urls")),
    path("clientes/", include("apps.crm.urls")),
    path("produtos/", include("apps.catalogo.urls")),
    path("fornecedores/", include("apps.fornecedores.urls")),
    path("pedidos/", include("apps.vendas.urls")),
    path("tarefas/", include("apps.tarefas.urls")),
    path("relatorios/", include("apps.relatorios.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
