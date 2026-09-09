from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("", views.ProdutoListView.as_view(), name="produto_lista"),
    path("novo/", views.ProdutoCreateView.as_view(), name="produto_novo"),
    path("<int:pk>/", views.ProdutoDetailView.as_view(), name="produto_detalhe"),
    path("<int:pk>/editar/", views.ProdutoUpdateView.as_view(), name="produto_editar"),
    path(
        "<int:pk>/excluir/", views.ProdutoDeleteView.as_view(), name="produto_excluir"
    ),
    path(
        "<int:pk>/movimentar/",
        views.MovimentacaoCreateView.as_view(),
        name="movimentacao_nova",
    ),
    path("movimentacoes/", views.MovimentacaoListView.as_view(), name="movimentacoes"),
    path("exportar/", views.exportar_inventario, name="inventario_exportar"),
]
