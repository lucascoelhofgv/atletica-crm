"""``/api/clientes/`` e apoio (categorias, tags)."""

from django.utils import timezone
from django_filters import rest_framework as filtros
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import PerfilModulo

from . import services
from .models import CategoriaCliente, Cliente, Interacao, Tag
from .serializers import (
    CategoriaClienteSerializer, ClienteListaSerializer, ClienteSerializer,
    InteracaoSerializer, OpcoesClienteSerializer, TagSerializer,
)


def _choices(enum):
    return [{"valor": v, "rotulo": r} for v, r in enum.choices]


class ClienteFiltro(filtros.FilterSet):
    fgv = filtros.BooleanFilter(field_name="membro_fgv")
    tag = filtros.NumberFilter(field_name="tags__id")

    class Meta:
        model = Cliente
        fields = ["categoria", "relacionamento", "vinculo", "fgv", "tag", "aceita_comunicacoes"]


class ClienteViewSet(viewsets.ModelViewSet):
    modulo = "crm"
    permission_classes = [IsAuthenticated, PerfilModulo]
    filterset_class = ClienteFiltro
    ordering_fields = ["nome", "criado_em", "qtd_pedidos", "total_gasto_calc"]
    ordering = ["nome"]

    def get_queryset(self):
        qs = Cliente.objects.select_related("categoria", "criado_por").prefetch_related("tags")
        qs = services.com_totais(qs)
        if self.action == "retrieve":
            qs = qs.prefetch_related("interacoes__registrado_por")
        return services.buscar(qs, self.request.query_params.get("q", ""))

    def filter_queryset(self, queryset):
        # SearchFilter fica de fora: a busca é a do serviço (mesma da tela antiga).
        for backend in self.filter_backends:
            if backend.__name__ == "SearchFilter":
                continue
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def get_serializer_class(self):
        return ClienteListaSerializer if self.action == "list" else ClienteSerializer

    def perform_create(self, serializer):
        cliente = serializer.save(criado_por=self.request.user)
        services.registrar(self.request.user, "cadastrou cliente", cliente)

    def perform_update(self, serializer):
        cliente = serializer.save()
        services.registrar(self.request.user, "editou cliente", cliente)

    def perform_destroy(self, instance):
        services.registrar(self.request.user, "excluiu cliente", instance)
        instance.delete()

    @action(detail=False, methods=["get"])
    def opcoes(self, request):
        dados = {
            "categorias": CategoriaCliente.objects.filter(ativo=True),
            "tags": Tag.objects.all(),
            "vinculos": _choices(Cliente.Vinculo),
            "relacionamentos": _choices(Cliente.Relacionamento),
            "tipos_interacao": _choices(Interacao.Tipo),
        }
        return Response(OpcoesClienteSerializer(dados).data)

    @action(detail=False, methods=["get"])
    def exportar(self, request):
        return services.exportar_csv(self.filter_queryset(self.get_queryset()))

    @action(detail=True, methods=["get", "post"])
    def interacoes(self, request, pk=None):
        cliente = self.get_object()
        if request.method == "GET":
            qs = cliente.interacoes.select_related("registrado_por")
            return Response(InteracaoSerializer(qs, many=True).data)
        serializer = InteracaoSerializer(data={"data": timezone.now(), **request.data})
        serializer.is_valid(raise_exception=True)
        interacao = serializer.save(cliente=cliente, registrado_por=request.user)
        services.registrar(request.user, "registrou interação com", cliente)
        return Response(InteracaoSerializer(interacao).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"interacoes/(?P<interacao_id>\d+)")
    def excluir_interacao(self, request, pk=None, interacao_id=None):
        cliente = self.get_object()
        apagadas, _ = cliente.interacoes.filter(pk=interacao_id).delete()
        if not apagadas:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoriaClienteViewSet(viewsets.ModelViewSet):
    modulo = "crm"
    permission_classes = [IsAuthenticated, PerfilModulo]
    queryset = CategoriaCliente.objects.all()
    serializer_class = CategoriaClienteSerializer
    pagination_class = None
    filterset_fields = ["ativo"]


class TagViewSet(viewsets.ModelViewSet):
    modulo = "crm"
    permission_classes = [IsAuthenticated, PerfilModulo]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


def registrar(router):
    router.register("clientes", ClienteViewSet, basename="cliente")
    router.register("categorias-cliente", CategoriaClienteViewSet, basename="categoria-cliente")
    router.register("tags", TagViewSet, basename="tag")
