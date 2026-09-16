"""``/api/eventos/`` com lotes, custos e receitas aninhados."""

from django_filters import rest_framework as filtros
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import PerfilModulo
from apps.contas.models import Membro
from apps.fornecedores.models import Fornecedor

from . import services
from .models import CustoEvento, Evento, LoteIngresso, ReceitaEvento
from .serializers import (
    CustoSerializer, EventoListaSerializer, EventoSerializer, LoteSerializer, OpcoesEventoSerializer,
    ReceitaSerializer,
)


def _choices(enum):
    return [{"valor": v, "rotulo": r} for v, r in enum.choices]


class EventoFiltro(filtros.FilterSet):
    inicio = filtros.DateFilter(field_name="data", lookup_expr="gte")
    fim = filtros.DateFilter(field_name="data", lookup_expr="lte")
    futuros = filtros.BooleanFilter(method="so_futuros")

    class Meta:
        model = Evento
        fields = ["tipo", "status", "responsavel", "inicio", "fim", "futuros"]

    def so_futuros(self, qs, nome, valor):
        from django.utils import timezone

        return qs.filter(data__gte=timezone.localdate()) if valor else qs


LINHAS = {
    "lotes": (LoteIngresso, LoteSerializer, "lote"),
    "custos": (CustoEvento, CustoSerializer, "custo"),
    "receitas": (ReceitaEvento, ReceitaSerializer, "receita"),
}


class EventoViewSet(viewsets.ModelViewSet):
    modulo = "eventos"
    permission_classes = [IsAuthenticated, PerfilModulo]
    filterset_class = EventoFiltro
    ordering_fields = ["data", "nome", "criado_em"]
    ordering = ["-data"]

    def get_queryset(self):
        qs = (Evento.objects.select_related("responsavel", "criado_por")
              .prefetch_related("lotes", "custos__fornecedor", "receitas", "fornecedores"))
        return services.buscar(qs, self.request.query_params.get("q", ""))

    def filter_queryset(self, queryset):
        for backend in self.filter_backends:
            if backend.__name__ == "SearchFilter":
                continue
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def get_serializer_class(self):
        return EventoListaSerializer if self.action == "list" else EventoSerializer

    def _responder(self, e, codigo=status.HTTP_200_OK):
        e = self.get_queryset().get(pk=e.pk)
        return Response(EventoSerializer(e, context={"request": self.request}).data, status=codigo)

    def perform_create(self, serializer):
        e = serializer.save(criado_por=self.request.user)
        services.registrar(self.request.user, "criou evento", e)

    def perform_update(self, serializer):
        e = serializer.save()
        services.registrar(self.request.user, "editou evento", e)

    def perform_destroy(self, instance):
        services.registrar(self.request.user, "excluiu evento", instance)
        instance.delete()

    @action(detail=False, methods=["get"])
    def opcoes(self, request):
        return Response(OpcoesEventoSerializer({
            "tipos": _choices(Evento.Tipo),
            "status": _choices(Evento.Status),
            "tipos_custo": _choices(CustoEvento.Tipo),
            "situacoes_custo": _choices(CustoEvento.Situacao),
            "origens_receita": _choices(ReceitaEvento.Origem),
            "membros": Membro.objects.filter(is_active=True).order_by("first_name", "username"),
            "fornecedores": Fornecedor.objects.filter(status=Fornecedor.Status.ATIVO).order_by("nome"),
        }).data)

    # --- linhas aninhadas (lotes, custos, receitas) --------------------------
    def _adicionar(self, request, pk, chave):
        modelo, serializer_cls, rotulo = LINHAS[chave]
        e = self.get_object()
        s = serializer_cls(data=request.data)
        s.is_valid(raise_exception=True)
        s.save(evento=e)
        services.registrar(request.user, f"adicionou {rotulo} em", e)
        return self._responder(e, status.HTTP_201_CREATED)

    def _alterar(self, request, pk, chave, linha_id):
        modelo, serializer_cls, rotulo = LINHAS[chave]
        e = self.get_object()
        try:
            linha = modelo.objects.get(pk=linha_id, evento=e)
        except modelo.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if request.method == "DELETE":
            linha.delete()
            services.registrar(request.user, f"removeu {rotulo} de", e)
            return self._responder(e)
        s = serializer_cls(linha, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        services.registrar(request.user, f"editou {rotulo} de", e)
        return self._responder(e)

    @action(detail=True, methods=["post"])
    def lotes(self, request, pk=None):
        return self._adicionar(request, pk, "lotes")

    @action(detail=True, methods=["patch", "delete"], url_path=r"lotes/(?P<linha_id>\d+)")
    def lote(self, request, pk=None, linha_id=None):
        return self._alterar(request, pk, "lotes", linha_id)

    @action(detail=True, methods=["post"])
    def custos(self, request, pk=None):
        return self._adicionar(request, pk, "custos")

    @action(detail=True, methods=["patch", "delete"], url_path=r"custos/(?P<linha_id>\d+)")
    def custo(self, request, pk=None, linha_id=None):
        return self._alterar(request, pk, "custos", linha_id)

    @action(detail=True, methods=["post"])
    def receitas(self, request, pk=None):
        return self._adicionar(request, pk, "receitas")

    @action(detail=True, methods=["patch", "delete"], url_path=r"receitas/(?P<linha_id>\d+)")
    def receita(self, request, pk=None, linha_id=None):
        return self._alterar(request, pk, "receitas", linha_id)


def registrar(router):
    router.register("eventos", EventoViewSet, basename="evento")
