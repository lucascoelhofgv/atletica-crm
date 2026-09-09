from django.urls import path

from . import views

app_name = "eventos"

urlpatterns = [
    path("", views.EventoListView.as_view(), name="lista"),
    path("novo/", views.EventoCreateView.as_view(), name="novo"),
    path("<int:pk>/", views.EventoDetailView.as_view(), name="detalhe"),
    path("<int:pk>/editar/", views.EventoUpdateView.as_view(), name="editar"),
    path("<int:pk>/excluir/", views.EventoDeleteView.as_view(), name="excluir"),
    path("<int:pk>/lote/", views.lote_add, name="lote_add"),
    path("<int:pk>/lote/<int:lote_id>/remover/", views.lote_del, name="lote_del"),
    path("<int:pk>/custo/", views.custo_add, name="custo_add"),
    path("<int:pk>/custo/<int:custo_id>/remover/", views.custo_del, name="custo_del"),
    path("<int:pk>/receita/", views.receita_add, name="receita_add"),
    path(
        "<int:pk>/receita/<int:receita_id>/remover/",
        views.receita_del, name="receita_del",
    ),
    path("festas/sincronizar/", views.sincronizar_festas, name="sheets_festas"),
]
