from django.urls import path

from . import views

app_name = "crm"

urlpatterns = [
    path("", views.ClienteListView.as_view(), name="cliente_lista"),
    path("novo/", views.ClienteCreateView.as_view(), name="cliente_novo"),
    path("<int:pk>/", views.ClienteDetailView.as_view(), name="cliente_detalhe"),
    path("<int:pk>/editar/", views.ClienteUpdateView.as_view(), name="cliente_editar"),
    path("<int:pk>/excluir/", views.ClienteDeleteView.as_view(), name="cliente_excluir"),
    path(
        "<int:pk>/interacao/",
        views.InteracaoCreateView.as_view(),
        name="interacao_nova",
    ),
    path("importar/", views.importar_clientes, name="cliente_importar"),
    path("exportar/", views.exportar_clientes, name="cliente_exportar"),
]
