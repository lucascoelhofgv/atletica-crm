"""Só o fluxo de recuperação de senha por e-mail continua server-rendered
(token, e-mail e templates já prontos). Login, logout, membros e "meus dados"
vivem no SPA e na API."""

from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

app_name = "contas"

urlpatterns = [
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
        auth_views.PasswordResetDoneView.as_view(template_name="contas/senha_enviada.html"),
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
        auth_views.PasswordResetCompleteView.as_view(template_name="contas/senha_concluida.html"),
        name="senha_concluida",
    ),
]
