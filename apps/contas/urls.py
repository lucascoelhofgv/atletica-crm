from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = "contas"

urlpatterns = [
    path(
        "entrar/",
        auth_views.LoginView.as_view(
            template_name="contas/login.html", redirect_authenticated_user=True
        ),
        name="login",
    ),
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
    # Recuperação de senha
    path(
        "senha/",
        auth_views.PasswordResetView.as_view(
            template_name="contas/senha_reset.html",
            email_template_name="contas/senha_reset_email.txt",
            subject_template_name="contas/senha_reset_assunto.txt",
            success_url=reverse_lazy("contas:senha_enviada"),
        ),
        name="senha_reset",
    ),
    path(
        "senha/enviada/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="contas/senha_enviada.html"
        ),
        name="senha_enviada",
    ),
    path(
        "senha/redefinir/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="contas/senha_confirmar.html",
            success_url=reverse_lazy("contas:senha_concluida"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "senha/concluida/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="contas/senha_concluida.html"
        ),
        name="senha_concluida",
    ),
    path(
        "senha/alterar/",
        auth_views.PasswordChangeView.as_view(
            template_name="contas/senha_alterar.html",
            success_url=reverse_lazy("contas:meus_dados"),
        ),
        name="senha_alterar",
    ),
    # Gestão de membros
    path("membros/", views.MembroListView.as_view(), name="membro_lista"),
    path("membros/novo/", views.MembroCreateView.as_view(), name="membro_novo"),
    path("membros/<int:pk>/", views.MembroUpdateView.as_view(), name="membro_editar"),
    path(
        "membros/<int:pk>/alternar/",
        views.membro_alternar_ativo,
        name="membro_alternar",
    ),
    path("meus-dados/", views.MeusDadosView.as_view(), name="meus_dados"),
]
