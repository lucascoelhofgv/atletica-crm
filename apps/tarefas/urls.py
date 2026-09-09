from django.urls import path

from . import views

app_name = "tarefas"

urlpatterns = [
    path("", views.TarefaListView.as_view(), name="lista"),
    path("quadro/", views.quadro, name="quadro"),
    path("nova/", views.TarefaCreateView.as_view(), name="nova"),
    path("<int:pk>/", views.TarefaDetailView.as_view(), name="detalhe"),
    path("<int:pk>/editar/", views.TarefaUpdateView.as_view(), name="editar"),
    path("<int:pk>/excluir/", views.TarefaDeleteView.as_view(), name="excluir"),
    path("<int:pk>/status/", views.mudar_status, name="status"),
    path("<int:pk>/comentar/", views.comentar, name="comentar"),
]
