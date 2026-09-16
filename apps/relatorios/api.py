"""``/api/relatorios/*``. Todos aceitam ``?formato=csv`` (mesmo arquivo da
tela antiga). Vendas e produtos usam o período compartilhado
(``?periodo=...``); estoque e clientes são fotos do momento."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import PerfilModulo
from apps.nucleo.services import periodos

from . import services


class _Relatorio(APIView):
    modulo = "relatorios"
    permission_classes = [IsAuthenticated, PerfilModulo]

    def quer_csv(self):
        return self.request.query_params.get("formato") == "csv"


class VendasView(_Relatorio):
    def get(self, request):
        periodo = periodos.resolver(request.query_params)
        if self.quer_csv():
            return services.vendas_csv(periodo)
        return Response(services.vendas_periodo(periodo))


class ProdutosView(_Relatorio):
    def get(self, request):
        periodo = periodos.resolver(request.query_params)
        if self.quer_csv():
            return services.produtos_csv(periodo.inicio, periodo.fim)
        dados = services.produtos_vendidos(periodo.inicio, periodo.fim)
        dados["periodo"] = periodo.como_dict()
        return Response(dados)


class EstoqueView(_Relatorio):
    def get(self, request):
        situacao = request.query_params.get("situacao") or None
        if self.quer_csv():
            return services.estoque_csv(situacao)
        dados = services.estoque_atual(situacao)
        dados.pop("produtos", None)
        return Response(dados)


class ClientesView(_Relatorio):
    def get(self, request):
        recorrentes = request.query_params.get("recorrentes") in ("1", "true")
        if self.quer_csv():
            return services.clientes_csv(recorrentes)
        return Response(services.clientes_dict(recorrentes))
