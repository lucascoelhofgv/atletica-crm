"""Registro do histórico de acessos (seção 3 do escopo)."""

from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver


def _dados_request(request):
    if request is None:
        return None, ""
    ip = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ip = ip.split(",")[0].strip() or request.META.get("REMOTE_ADDR")
    agente = request.META.get("HTTP_USER_AGENT", "")[:255]
    return ip or None, agente


@receiver(user_logged_in)
def registrar_login(sender, request, user, **kwargs):
    from apps.nucleo.models import LogAcesso

    ip, agente = _dados_request(request)
    LogAcesso.objects.create(usuario=user, ip=ip, agente=agente, sucesso=True)


@receiver(user_login_failed)
def registrar_falha(sender, credentials, request, **kwargs):
    from django.contrib.auth import get_user_model

    from apps.nucleo.models import LogAcesso

    User = get_user_model()
    username = (credentials or {}).get("username", "")
    user = User.objects.filter(username=username).first()
    ip, agente = _dados_request(request)
    LogAcesso.objects.create(usuario=user, ip=ip, agente=agente, sucesso=False)
