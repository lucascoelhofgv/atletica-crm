"""``/api/produtos/``, ``/api/movimentacoes/`` e ``/api/categorias-produto/``."""

from django_filters import rest_framework as filtros
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import PerfilModulo
from apps.fornecedores.models import Fornecedor

from . import services
from .models import CategoriaProduto, MovimentacaoEstoque, Produto
from .serializers import (
    CategoriaProdutoSerializer, MovimentacaoEntradaSerializer, MovimentacaoSerializer,
    OpcoesProdutoSerializer, ProdutoListaSerializer, ProdutoSerializer,
)


def _choices(enum):
    return [{"valor": v, "rotulo": r} for v, r in enum.choices]


class ProdutoFiltro(filtros.FilterSet):
    situacao = filtros.CharFilter(method="por_situacao")

    class Meta:
        model = Produto
        fields = ["categoria", "fornecedor", "status", "situacao"]

    def por_situacao(self, qs, nome, valor):
        return services.filtrar_situacao(qs, valor)


class ProdutoViewSet(viewsets.ModelViewSet):
    modulo = "catalogo"
    permission_classes = [IsAuthenticated, PerfilModulo]
    parser_classes = [JSONParser, MultiPartParser, FormParser]  # foto via multipart
    filterset_class = ProdutoFiltro
    ordering_fields = ["nome", "quantidade_atual", "preco_venda", "custo_unitario", "criado_em"]
    ordering = ["nome"]

    def get_queryset(self):
        qs = Produto.objects.select_related("categoria", "fornecedor", "criado_por")
        return services.buscar(qs, self.request.query_params.get("q", ""))

    def filter_queryset(self, queryset):
        for backend in self.filter_backends:
            if backend.__name__ == "SearchFilter":
                continue
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def get_serializer_class(self):
        return ProdutoListaSerializer if self.action == "list" else ProdutoSerializer

    def perform_create(self, serializer):
        produto = serializer.save(criado_por=self.request.user)
        services.registrar(self.request.user, "cadastrou produto", produto)

    def perform_update(self, serializer):
        produto = serializer.save()
        services.registrar(self.request.user, "editou produto", produto)

    def perform_destroy(self, instance):
        services.registrar(self.request.user, "excluiu produto", instance)
        instance.delete()

    @action(detail=False, methods=["get"])
    def opcoes(self, request):
        dados = {
            "categorias": CategoriaProduto.objects.filter(ativo=True),
            "fornecedores": Fornecedor.objects.filter(status=Fornecedor.Status.ATIVO).order_by("nome"),
            "status": _choices(Produto.Status),
            "tipos_movimentacao": _choices(MovimentacaoEstoque.Tipo),
        }
        return Response(OpcoesProdutoSerializer(dados).data)

    @action(detail=False, methods=["get"])
    def exportar(self, request):
        return services.exportar_csv(self.filter_queryset(self.get_queryset()))

    @action(detail=True, methods=["post"])
    def movimentar(self, request, pk=None):
        produto = self.get_object()
        entrada = MovimentacaoEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        mov = services.movimentar(produto, usuario=request.user, **entrada.validated_data)
        produto.refresh_from_db()
        return Response(
            {"movimentacao": MovimentacaoSerializer(mov).data,
             "produto": ProdutoSerializer(produto, context={"request": request}).data},
            status=status.HTTP_201_CREATED,
        )


class MovimentacaoViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    modulo = "catalogo"
    permission_classes = [IsAuthenticated, PerfilModulo]
    serializer_class = MovimentacaoSerializer
    filterset_fields = ["produto", "tipo", "usuario"]
    ordering = ["-data"]

    def get_queryset(self):
        return MovimentacaoEstoque.objects.select_related("produto", "usuario", "pedido")


class CategoriaProdutoViewSet(viewsets.ModelViewSet):
    modulo = "catalogo"
    permission_classes = [IsAuthenticated, PerfilModulo]
    queryset = CategoriaProduto.objects.all()
    serializer_class = CategoriaProdutoSerializer
    pagination_class = None
    filterset_fields = ["ativo"]


def registrar(router):
    router.register("produtos", ProdutoViewSet, basename="produto")
    router.register("movimentacoes", MovimentacaoViewSet, basename="movimentacao")
    router.register("categorias-produto", CategoriaProdutoViewSet, basename="categoria-produto")
