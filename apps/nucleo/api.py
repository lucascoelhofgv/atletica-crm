"""Endpoints do núcleo: configuração (white-label), atividades e acessos."""

from rest_framework import mixins, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import SomenteAdmin

from .models import Configuracao, LogAcesso, RegistroAtividade, registrar_atividade
from .serializers import (
    ConfiguracaoSerializer, LogAcessoSerializer, RegistroAtividadeSerializer,
)


class ConfigView(APIView):
    """GET é público (login precisa do logo/cores); PATCH só para administrador."""

    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated(), SomenteAdmin()]

    def get(self, request):
        cfg = Configuracao.carregar()
        return Response(ConfiguracaoSerializer(cfg, context={"request": request}).data)

    def patch(self, request):
        cfg = Configuracao.carregar()
        serializer = ConfiguracaoSerializer(
            cfg, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        registrar_atividade(request.user, "atualizou a identidade visual")
        return Response(serializer.data)


class BuscaView(APIView):
    """Busca global: grupos por módulo, respeitando o que o usuário pode ler."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .services.busca import buscar

        termo = request.query_params.get("q", "")
        return Response({"termo": termo, "grupos": buscar(termo, request.user)})


class DashboardView(APIView):
    """Tudo que o painel precisa em uma chamada (menos round-trips no cold
    start do Render). Parâmetros: ver ``services/periodos.py``."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .services import dashboard, periodos

        periodo = periodos.resolver(request.query_params)
        return Response(dashboard.montar(periodo, request.user))


class AtividadeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = RegistroAtividadeSerializer
    queryset = RegistroAtividade.objects.select_related("usuario")
    search_fields = ["verbo", "alvo", "descricao", "usuario__first_name",
                     "usuario__last_name", "usuario__username"]
    ordering = ["-criado_em"]


class LogAcessoViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = LogAcessoSerializer
    ordering = ["-momento"]

    def get_queryset(self):
        qs = LogAcesso.objects.select_related("usuario")
        if not self.request.user.eh_admin:
            qs = qs.filter(usuario=self.request.user)
        return qs


def registrar(router):
    router.register("atividades", AtividadeViewSet, basename="atividade")
    router.register("acessos", LogAcessoViewSet, basename="acesso")
