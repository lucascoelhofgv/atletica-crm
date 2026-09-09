from django.urls import path

from . import views

app_name = "nucleo"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("configuracao/", views.ConfiguracaoUpdateView.as_view(), name="configuracao"),
    path("busca/", views.busca_global, name="busca"),
    path("integracoes/sheets/", views.sincronizar_sheets, name="sheets"),
    path("atividades/", views.AtividadeListView.as_view(), name="atividades"),
    path("acessos/", views.LogAcessoListView.as_view(), name="acessos"),
]
