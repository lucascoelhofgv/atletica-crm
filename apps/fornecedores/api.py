"""``/api/fornecedores/``."""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import PerfilModulo

from . import services
from .models import AvaliacaoFornecedor, Fornecedor
from .serializers import (
    AvaliacaoSerializer, FornecedorListaSerializer, FornecedorSerializer, OpcoesFornecedorSerializer,
)


def _choices(enum):
    return [{"valor": v, "rotulo": r} for v, r in enum.choices]


class FornecedorViewSet(viewsets.ModelViewSet):
    modulo = "fornecedores"
    permission_classes = [IsAuthenticated, PerfilModulo]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filterset_fields = ["categoria", "status"]
    ordering_fields = ["nome", "criado_em", "nota_media_calc", "qtd_produtos"]
    ordering = ["nome"]

    def get_queryset(self):
        qs = services.com_totais(Fornecedor.objects.select_related("criado_por"))
        if self.action == "retrieve":
            qs = qs.prefetch_related("avaliacoes__autor", "produtos")
        return services.buscar(qs, self.request.query_params.get("q", ""))

    def filter_queryset(self, queryset):
        for backend in self.filter_backends:
            if backend.__name__ == "SearchFilter":
                continue
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def get_serializer_class(self):
        return FornecedorListaSerializer if self.action == "list" else FornecedorSerializer

    def _responder(self, f, codigo=status.HTTP_200_OK):
        f = self.get_queryset().get(pk=f.pk)
        return Response(FornecedorSerializer(f, context={"request": self.request}).data, status=codigo)

    def perform_create(self, serializer):
        f = serializer.save(criado_por=self.request.user)
        services.registrar(self.request.user, "cadastrou fornecedor", f)

    def perform_update(self, serializer):
        f = serializer.save()
        services.registrar(self.request.user, "editou fornecedor", f)

    def perform_destroy(self, instance):
        services.registrar(self.request.user, "excluiu fornecedor", instance)
        instance.delete()

    @action(detail=False, methods=["get"])
    def opcoes(self, request):
        return Response(OpcoesFornecedorSerializer({
            "categorias": _choices(Fornecedor.Categoria), "status": _choices(Fornecedor.Status),
        }).data)

    @action(detail=True, methods=["post"])
    def avaliacoes(self, request, pk=None):
        f = self.get_object()
        s = AvaliacaoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save(fornecedor=f, autor=request.user)
        services.registrar(request.user, "avaliou fornecedor", f)
        return self._responder(f, status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"avaliacoes/(?P<avaliacao_id>\d+)")
    def excluir_avaliacao(self, request, pk=None, avaliacao_id=None):
        f = self.get_object()
        apagadas, _ = AvaliacaoFornecedor.objects.filter(fornecedor=f, pk=avaliacao_id).delete()
        if not apagadas:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return self._responder(f)

    @action(detail=True, methods=["post"])
    def contrato(self, request, pk=None):
        f = self.get_object()
        arquivo = request.FILES.get("contrato")
        if arquivo is None:
            f.contrato.delete(save=False)
            f.contrato = None
        else:
            f.contrato = arquivo
        f.save(update_fields=["contrato"])
        return self._responder(f)


def registrar(router):
    router.register("fornecedores", FornecedorViewSet, basename="fornecedor")
