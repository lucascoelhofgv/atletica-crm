"""Autenticação por sessão para o SPA.

Fluxo: o frontend chama ``GET /api/auth/me/`` (que também garante o cookie
``csrftoken``); recebe 401 se não há sessão e mostra o login; ``POST
/api/auth/login/`` cria a sessão (os sinais de ``apps.contas.signals``
gravam o ``LogAcesso`` como sempre). O login exige CSRF (``csrf_protect``)
mesmo sem sessão, para evitar *login CSRF*.
"""

from django.contrib.auth import (
    authenticate, get_user_model, login, logout, update_session_auth_hash,
)
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import serializers, status
from rest_framework.exceptions import NotAuthenticated, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.nucleo.models import registrar_atividade
from apps.nucleo.serializers import MembroAtualSerializer


def _dados_usuario(user, request):
    return MembroAtualSerializer(user, context={"request": request}).data


class CsrfView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({"ok": True})


class MeView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        if not request.user.is_authenticated:
            raise NotAuthenticated()
        return Response(_dados_usuario(request.user, request))

    def patch(self, request):
        """Meus dados: nome, e-mail, telefone e foto do próprio usuário."""
        if not request.user.is_authenticated:
            raise NotAuthenticated()
        from apps.contas.serializers import MeusDadosSerializer

        s = MeusDadosSerializer(request.user, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        registrar_atividade(request.user, "atualizou os próprios dados")
        return Response(_dados_usuario(request.user, request))


class LoginSerializer(serializers.Serializer):
    usuario = serializers.CharField(help_text="username ou e-mail")
    senha = serializers.CharField(trim_whitespace=False)


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # sem sessão prévia: o csrf_protect já cobre

    def post(self, request):
        dados = LoginSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        identificador = dados.validated_data["usuario"].strip()
        senha = dados.validated_data["senha"]

        username = identificador
        if "@" in identificador:
            Membro = get_user_model()
            username = (
                Membro.objects.filter(email__iexact=identificador)
                .values_list("username", flat=True).first()
                or identificador
            )

        user = authenticate(request, username=username, password=senha)
        if user is None:
            raise ValidationError(
                {"non_field_errors": ["Usuário ou senha inválidos."]}
            )
        login(request, user)
        return Response(_dados_usuario(user, request))


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SenhaSerializer(serializers.Serializer):
    senha_atual = serializers.CharField(trim_whitespace=False)
    senha_nova = serializers.CharField(trim_whitespace=False)
    senha_nova_confirmacao = serializers.CharField(trim_whitespace=False)


_CAMPOS_FORM = {
    "old_password": "senha_atual",
    "new_password1": "senha_nova",
    "new_password2": "senha_nova_confirmacao",
}


class SenhaView(APIView):
    """Troca de senha do usuário logado. Reaproveita o ``PasswordChangeForm``
    do Django para manter os mesmos validadores das páginas antigas."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        dados = SenhaSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        v = dados.validated_data
        form = PasswordChangeForm(request.user, data={
            "old_password": v["senha_atual"],
            "new_password1": v["senha_nova"],
            "new_password2": v["senha_nova_confirmacao"],
        })
        if not form.is_valid():
            erros = {
                _CAMPOS_FORM.get(campo, campo): [str(m) for m in mensagens]
                for campo, mensagens in form.errors.items()
            }
            raise ValidationError(erros)
        form.save()
        update_session_auth_hash(request, form.user)
        registrar_atividade(request.user, "alterou a própria senha")
        return Response({"ok": True})
