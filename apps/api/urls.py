"""Roteamento de ``/api/``.

Cada app expõe uma função ``registrar(router)`` em ``apps/<app>/api.py`` que
registra seus ViewSets. Rotas avulsas (auth, config, dashboard) entram aqui.
A última rota devolve 404 em JSON para qualquer caminho desconhecido.
"""

from django.urls import path, re_path
from rest_framework.routers import DefaultRouter

from apps.catalogo import api as catalogo_api
from apps.contas import api as contas_api
from apps.crm import api as crm_api
from apps.eventos import api as eventos_api
from apps.fornecedores import api as fornecedores_api
from apps.nucleo import api as nucleo_api
from apps.nucleo import api_integracoes as integ
from apps.nucleo.api import BuscaView, ConfigView, DashboardView
from apps.relatorios import api as relatorios_api
from apps.tarefas import api as tarefas_api
from apps.vendas import api as vendas_api

from .views_auth import CsrfView, LoginView, LogoutView, MeView, SenhaView
from .views_saude import nao_encontrado, saude

router = DefaultRouter()
nucleo_api.registrar(router)
crm_api.registrar(router)
catalogo_api.registrar(router)
vendas_api.registrar(router)
fornecedores_api.registrar(router)
tarefas_api.registrar(router)
eventos_api.registrar(router)
contas_api.registrar(router)

urlpatterns = [
    path("saude/", saude, name="api_saude"),
    path("auth/csrf/", CsrfView.as_view(), name="api_csrf"),
    path("auth/me/", MeView.as_view(), name="api_me"),
    path("auth/login/", LoginView.as_view(), name="api_login"),
    path("auth/logout/", LogoutView.as_view(), name="api_logout"),
    path("auth/senha/", SenhaView.as_view(), name="api_senha"),
    path("config/", ConfigView.as_view(), name="api_config"),
    path("dashboard/", DashboardView.as_view(), name="api_dashboard"),
    path("busca/", BuscaView.as_view(), name="api_busca"),
    path("integracoes/sheets/", integ.SheetsView.as_view(), name="api_sheets"),
    path("integracoes/sheets/exportar/", integ.ExportarSheetsView.as_view(), name="api_sheets_exportar"),
    path("integracoes/sheets/festas/", integ.ExportarFestasView.as_view(), name="api_sheets_festas"),
    path("integracoes/importar/previa/", integ.PreviaImportacaoView.as_view(), name="api_importar_previa"),
    path("integracoes/importar/", integ.ImportarView.as_view(), name="api_importar"),
    path("relatorios/vendas/", relatorios_api.VendasView.as_view(), name="api_rel_vendas"),
    path("relatorios/produtos/", relatorios_api.ProdutosView.as_view(), name="api_rel_produtos"),
    path("relatorios/estoque/", relatorios_api.EstoqueView.as_view(), name="api_rel_estoque"),
    path("relatorios/clientes/", relatorios_api.ClientesView.as_view(), name="api_rel_clientes"),
    *router.urls,
    re_path(r"^.*$", nao_encontrado),
]
