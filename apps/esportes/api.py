"""``/api/esportes/``: resumo orçado x realizado e a lista de treinos e jogos.

Só leitura: os dados vêm das planilhas de Esportes pela sincronização das
Fontes de planilha, e a planilha continua sendo onde a diretoria edita.
"""

from django_filters import rest_framework as filtros
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import PerfilModulo

from . import services
from .models import Sessao, meses_do_semestre


class SessaoSerializer(serializers.ModelSerializer):
    modalidade_nome = serializers.CharField(source="modalidade.nome", read_only=True)
    tipo_rotulo = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = Sessao
        fields = [
            "id", "modalidade", "modalidade_nome", "tipo", "tipo_rotulo", "data",
            "confirmada", "teve_tecnico", "teve_quadra", "custo_tecnico", "custo_quadra",
            "custo", "observacao", "origem",
        ]


class SessaoFiltro(filtros.FilterSet):
    ano = filtros.NumberFilter(field_name="data", lookup_expr="year")
    semestre = filtros.NumberFilter(method="do_semestre")
    esporte = filtros.CharFilter(field_name="modalidade__esporte")

    class Meta:
        model = Sessao
        fields = ["modalidade", "tipo", "confirmada", "ano", "semestre", "esporte"]

    def do_semestre(self, qs, nome, valor):
        if valor not in (1, 2):
            return qs
        meses = meses_do_semestre(int(valor))
        return qs.filter(data__month__gte=meses.start, data__month__lt=meses.stop)


class SessaoViewSet(viewsets.ReadOnlyModelViewSet):
    modulo = "esportes"
    permission_classes = [IsAuthenticated, PerfilModulo]
    serializer_class = SessaoSerializer
    filterset_class = SessaoFiltro
    ordering_fields = ["data", "custo"]
    ordering = ["-data"]
    queryset = Sessao.objects.select_related("modalidade")


class ResumoView(APIView):
    modulo = "esportes"
    permission_classes = [IsAuthenticated, PerfilModulo]

    def get(self, request):
        def inteiro(nome):
            try:
                return int(request.query_params.get(nome, ""))
            except ValueError:
                return None

        return Response(services.resumo(inteiro("ano"), inteiro("semestre")))


def registrar(router):
    router.register("esportes/sessoes", SessaoViewSet, basename="esporte-sessao")
