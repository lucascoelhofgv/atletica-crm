"""``/api/tarefas/``."""

from django.db.models import Count, F
from django_filters import rest_framework as filtros
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import PerfilModulo
from apps.contas.models import Membro

from . import services
from .models import ComentarioTarefa, Tarefa
from .serializers import (
    ComentarioSerializer, OpcoesTarefaSerializer, TarefaCartaoSerializer, TarefaSerializer,
)


def _choices(enum):
    return [{"valor": v, "rotulo": r} for v, r in enum.choices]


class TarefaFiltro(filtros.FilterSet):
    minhas = filtros.BooleanFilter(method="so_minhas")
    atrasadas = filtros.BooleanFilter(method="so_atrasadas")
    abertas = filtros.BooleanFilter(method="so_abertas")

    class Meta:
        model = Tarefa
        fields = ["status", "prioridade", "responsavel", "cliente", "pedido", "fornecedor",
                  "minhas", "atrasadas", "abertas"]

    def so_minhas(self, qs, nome, valor):
        return qs.filter(responsavel=self.request.user) if valor else qs

    def so_atrasadas(self, qs, nome, valor):
        return services.atrasadas(qs) if valor else qs

    def so_abertas(self, qs, nome, valor):
        return qs.filter(status__in=services.ABERTAS) if valor else qs


class TarefaViewSet(viewsets.ModelViewSet):
    modulo = "tarefas"
    permission_classes = [IsAuthenticated, PerfilModulo]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filterset_class = TarefaFiltro
    ordering_fields = ["prazo", "criado_em", "prioridade", "titulo"]
    ordering = [F("prazo").asc(nulls_last=True), "-criado_em"]

    def get_queryset(self):
        qs = (Tarefa.objects.select_related("responsavel", "criador", "cliente", "pedido", "fornecedor")
              .annotate(qtd_comentarios=Count("comentarios", distinct=True)))
        if self.action == "retrieve":
            qs = qs.prefetch_related("comentarios__autor")
        return services.buscar(qs, self.request.query_params.get("q", ""))

    def filter_queryset(self, queryset):
        for backend in self.filter_backends:
            if backend.__name__ == "SearchFilter":
                continue
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def get_serializer_class(self):
        return TarefaCartaoSerializer if self.action in ("list", "quadro") else TarefaSerializer

    def _responder(self, t, codigo=status.HTTP_200_OK):
        t = self.get_queryset().get(pk=t.pk)
        return Response(TarefaSerializer(t, context={"request": self.request}).data, status=codigo)

    def perform_create(self, serializer):
        t = serializer.save(criador=self.request.user)
        services.registrar(self.request.user, "criou tarefa", t)

    def perform_update(self, serializer):
        t = serializer.save()
        services.registrar(self.request.user, "editou tarefa", t)

    def perform_destroy(self, instance):
        services.registrar(self.request.user, "excluiu tarefa", instance)
        instance.delete()

    @action(detail=False, methods=["get"])
    def opcoes(self, request):
        return Response(OpcoesTarefaSerializer({
            "status": _choices(Tarefa.Status),
            "prioridades": _choices(Tarefa.Prioridade),
            "membros": Membro.objects.filter(is_active=True).order_by("first_name", "username"),
        }).data)

    @action(detail=False, methods=["get"])
    def quadro(self, request):
        """Colunas por status, com os mesmos filtros da lista (sem paginação)."""
        qs = self.filter_queryset(self.get_queryset())
        por_status = {valor: [] for valor, _ in Tarefa.Status.choices}
        for t in qs:
            por_status[t.status].append(t)
        colunas = [
            {"status": valor, "rotulo": rotulo,
             "tarefas": TarefaCartaoSerializer(por_status[valor], many=True, context={"request": request}).data}
            for valor, rotulo in Tarefa.Status.choices
        ]
        return Response({"colunas": colunas})

    @action(detail=True, methods=["post"])
    def mover(self, request, pk=None):
        t = self.get_object()
        try:
            services.mover(t, request.data.get("status"), request.user)
        except ValueError as exc:
            raise ValidationError({"status": [str(exc)]})
        return self._responder(t)

    @action(detail=True, methods=["post"])
    def comentarios(self, request, pk=None):
        t = self.get_object()
        s = ComentarioSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        services.comentar(t, s.validated_data["texto"], request.user)
        return self._responder(t, status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"comentarios/(?P<comentario_id>\d+)")
    def excluir_comentario(self, request, pk=None, comentario_id=None):
        t = self.get_object()
        qs = ComentarioTarefa.objects.filter(tarefa=t, pk=comentario_id)
        if not request.user.eh_admin:
            qs = qs.filter(autor=request.user)  # só o autor apaga o próprio comentário
        apagados, _ = qs.delete()
        if not apagados:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return self._responder(t)

    @action(detail=True, methods=["post"])
    def anexo(self, request, pk=None):
        t = self.get_object()
        arquivo = request.FILES.get("anexo")
        if arquivo is None:
            t.anexo.delete(save=False)
            t.anexo = None
        else:
            t.anexo = arquivo
        t.save(update_fields=["anexo"])
        return self._responder(t)


def registrar(router):
    router.register("tarefas", TarefaViewSet, basename="tarefa")
