"""``/api/pedidos/``."""

from django.db.models import Count
from django_filters import rest_framework as filtros
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import PerfilModulo
from apps.contas.models import Membro

from . import services
from .models import Pedido
from .serializers import (
    OpcoesPedidoSerializer, PagamentoSerializer, PedidoEntradaSerializer, PedidoListaSerializer,
    PedidoSerializer,
)


def _choices(enum):
    return [{"valor": v, "rotulo": r} for v, r in enum.choices]


class PedidoFiltro(filtros.FilterSet):
    inicio = filtros.DateFilter(field_name="data_compra", lookup_expr="gte")
    fim = filtros.DateFilter(field_name="data_compra", lookup_expr="lte")

    class Meta:
        model = Pedido
        fields = ["status", "status_pagamento", "forma_pagamento", "cliente", "responsavel",
                  "inicio", "fim"]


def _erro_estoque(exc: services.EstoqueInsuficiente):
    """400 no formato da API, mantendo os números das faltas (o ValidationError
    do DRF converteria tudo em texto)."""
    return Response(
        {"erro": {"codigo": "estoque_insuficiente", "mensagem": str(exc),
                  "campos": {"itens": exc.como_lista()}}},
        status=status.HTTP_400_BAD_REQUEST,
    )


class PodeRegistrarPagamento(BasePermission):
    """Financeiro registra pagamento mesmo sem poder editar pedidos."""

    message = "Só Administrador, Diretoria ou Financeiro registram pagamentos."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and services.pode_registrar_pagamento(request.user))


class PedidoViewSet(viewsets.ModelViewSet):
    modulo = "vendas"
    permission_classes = [IsAuthenticated, PerfilModulo]

    def get_permissions(self):
        if self.action in ("pagamentos", "excluir_pagamento"):
            return [IsAuthenticated(), PodeRegistrarPagamento()]
        return super().get_permissions()
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filterset_class = PedidoFiltro
    ordering_fields = ["data_compra", "criado_em", "valor_total", "numero"]
    ordering = ["-data_compra", "-id"]

    def get_queryset(self):
        qs = Pedido.objects.select_related("cliente", "responsavel", "criado_por")
        if self.action == "list":
            qs = qs.annotate(qtd_itens=Count("itens", distinct=True))
        else:
            qs = qs.prefetch_related("itens__produto", "pagamentos__registrado_por")
        return services.buscar(qs, self.request.query_params.get("q", ""))

    def filter_queryset(self, queryset):
        for backend in self.filter_backends:
            if backend.__name__ == "SearchFilter":
                continue
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def get_serializer_class(self):
        return PedidoListaSerializer if self.action == "list" else PedidoSerializer

    def _responder(self, pedido, codigo=status.HTTP_200_OK):
        pedido = self.get_queryset().get(pk=pedido.pk)
        return Response(PedidoSerializer(pedido, context={"request": self.request}).data, status=codigo)

    def create(self, request, *args, **kwargs):
        entrada = PedidoEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        dados = dict(entrada.validated_data)
        itens = dados.pop("itens", [])
        try:
            pedido = services.salvar_pedido(Pedido(), dados, itens, request.user)
        except services.EstoqueInsuficiente as exc:
            return _erro_estoque(exc)
        return self._responder(pedido, status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        pedido = self.get_object()
        entrada = PedidoEntradaSerializer(data=request.data, parcial=kwargs.get("partial", False))
        entrada.is_valid(raise_exception=True)
        dados = dict(entrada.validated_data)
        itens = dados.pop("itens", None)
        try:
            pedido = services.salvar_pedido(pedido, dados, itens, request.user)
        except services.EstoqueInsuficiente as exc:
            return _erro_estoque(exc)
        return self._responder(pedido)

    def perform_destroy(self, instance):
        services.excluir_pedido(instance, self.request.user)

    @action(detail=False, methods=["get"])
    def opcoes(self, request):
        dados = {
            "status": _choices(Pedido.Status),
            "formas_pagamento": _choices(Pedido.FormaPagamento),
            "status_pagamento": _choices(Pedido.StatusPagamento),
            "membros": Membro.objects.filter(is_active=True).order_by("first_name", "username"),
        }
        return Response(OpcoesPedidoSerializer(dados).data)

    @action(detail=True, methods=["post"], url_path="status")
    def mudar_status(self, request, pk=None):
        pedido = self.get_object()
        novo = request.data.get("status")
        if novo not in dict(Pedido.Status.choices):
            raise ValidationError({"status": ["Status inválido."]})
        try:
            services.mudar_status(pedido, novo, request.user)
        except services.EstoqueInsuficiente as exc:
            return _erro_estoque(exc)
        return self._responder(pedido)

    @action(detail=True, methods=["post"])
    def pagamentos(self, request, pk=None):
        pedido = self.get_object()
        dados = PagamentoSerializer(data=request.data)
        dados.is_valid(raise_exception=True)
        services.registrar_pagamento(pedido, dados.validated_data, request.user)
        return self._responder(pedido, status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"pagamentos/(?P<pagamento_id>\d+)")
    def excluir_pagamento(self, request, pk=None, pagamento_id=None):
        pedido = self.get_object()
        if not services.excluir_pagamento(pedido, int(pagamento_id), request.user):
            return Response(status=status.HTTP_404_NOT_FOUND)
        return self._responder(pedido)

    @action(detail=True, methods=["post"])
    def comprovante(self, request, pk=None):
        pedido = self.get_object()
        arquivo = request.FILES.get("comprovante")
        if arquivo is None:
            pedido.comprovante.delete(save=False)
            pedido.comprovante = None
        else:
            pedido.comprovante = arquivo
        pedido.save(update_fields=["comprovante"])
        return self._responder(pedido)


def registrar(router):
    router.register("pedidos", PedidoViewSet, basename="pedido")
