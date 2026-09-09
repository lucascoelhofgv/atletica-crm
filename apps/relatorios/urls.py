from django.urls import path

from . import views

app_name = "relatorios"

urlpatterns = [
    path("", views.indice, name="indice"),
    path("vendas/", views.vendas_periodo, name="vendas_periodo"),
    path("produtos/", views.produtos_vendidos, name="produtos_vendidos"),
    path("estoque/", views.estoque_atual, name="estoque_atual"),
    path("clientes/", views.clientes, name="clientes"),
]
