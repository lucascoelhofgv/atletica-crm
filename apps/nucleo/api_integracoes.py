"""``/api/integracoes/*`` (só administrador)."""

from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import SomenteAdmin

from .services import integracoes


def _erro_sheets(exc, codigo="sheets_indisponivel", http=status.HTTP_503_SERVICE_UNAVAILABLE):
    return Response({"erro": {"codigo": codigo, "mensagem": str(exc), "campos": {}}}, status=http)


class _Admin(APIView):
    permission_classes = [IsAuthenticated, SomenteAdmin]


class SheetsView(_Admin):
    def get(self, request):
        return Response(integracoes.situacao())


class ExportarSheetsView(_Admin):
    def post(self, request):
        try:
            return Response({"resumo": integracoes.exportar_sheets(request.user)})
        except integracoes.SheetsIndisponivel as exc:
            return _erro_sheets(exc)
        except Exception as exc:  # pragma: no cover - erro remoto do Google
            return _erro_sheets(exc, "sheets_falha", status.HTTP_502_BAD_GATEWAY)


class ExportarFestasView(_Admin):
    def post(self, request):
        try:
            return Response({"eventos": integracoes.exportar_festas(request.user)})
        except integracoes.SheetsIndisponivel as exc:
            return _erro_sheets(exc)
        except Exception as exc:  # pragma: no cover
            return _erro_sheets(exc, "sheets_falha", status.HTTP_502_BAD_GATEWAY)


class ImportacaoSerializer(serializers.Serializer):
    planilha = serializers.CharField(help_text="URL ou ID da planilha")
    aba = serializers.CharField(required=False, allow_blank=True, default="")
    destino = serializers.CharField()
    modo = serializers.ChoiceField(choices=["criar_atualizar", "somente_criar"], default="criar_atualizar")


class PreviaImportacaoView(_Admin):
    def post(self, request):
        s = ImportacaoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        v = s.validated_data
        try:
            return Response(integracoes.previa_importacao(v["planilha"], v["aba"], v["destino"]))
        except ValueError as exc:
            return _erro_sheets(exc, "validacao", status.HTTP_400_BAD_REQUEST)
        except integracoes.SheetsIndisponivel as exc:
            return _erro_sheets(exc)
        except Exception as exc:  # pragma: no cover
            return _erro_sheets(f"Não consegui ler a planilha: {exc}", "sheets_falha", status.HTTP_502_BAD_GATEWAY)


class ImportarView(_Admin):
    def post(self, request):
        s = ImportacaoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        v = s.validated_data
        try:
            return Response(integracoes.importar(v["planilha"], v["aba"], v["destino"], v["modo"], request.user))
        except ValueError as exc:
            return _erro_sheets(exc, "validacao", status.HTTP_400_BAD_REQUEST)
        except integracoes.SheetsIndisponivel as exc:
            return _erro_sheets(exc)
        except Exception as exc:  # pragma: no cover
            return _erro_sheets(f"Falha na importação: {exc}", "sheets_falha", status.HTTP_502_BAD_GATEWAY)


class FestaImportacaoSerializer(serializers.Serializer):
    planilha = serializers.CharField()
    aba = serializers.CharField(required=False, allow_blank=True, default="")
    linha_inicial = serializers.IntegerField(required=False, allow_null=True, default=None, min_value=1)
    nome = serializers.CharField(required=False, allow_blank=True, default="")
    data = serializers.DateField(required=False, allow_null=True, default=None)
    local = serializers.CharField(required=False, allow_blank=True, default="")
    capacidade = serializers.IntegerField(required=False, allow_null=True, default=None, min_value=0)
    staff = serializers.IntegerField(required=False, allow_null=True, default=0, min_value=0)


class PreviaFestaView(_Admin):
    def post(self, request):
        s = FestaImportacaoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        v = s.validated_data
        try:
            return Response(integracoes.previa_festa(v["planilha"], v["aba"] or None, v["linha_inicial"]))
        except integracoes.SheetsIndisponivel as exc:
            return _erro_sheets(exc)
        except Exception as exc:  # pragma: no cover
            return _erro_sheets(f"Não consegui ler a planilha: {exc}", "sheets_falha", status.HTTP_502_BAD_GATEWAY)


class ImportarFestaView(_Admin):
    def post(self, request):
        s = FestaImportacaoSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        v = s.validated_data
        if not v["nome"] or not v["data"]:
            return _erro_sheets("Informe nome e data da festa.", "validacao", status.HTTP_400_BAD_REQUEST)
        try:
            resultado = integracoes.importar_festa(
                v["planilha"], v["aba"] or None, v["linha_inicial"], v["nome"], v["data"],
                v["local"], v["capacidade"], v["staff"], request.user,
            )
            return Response(resultado)
        except ValueError as exc:
            return _erro_sheets(exc, "validacao", status.HTTP_400_BAD_REQUEST)
        except integracoes.SheetsIndisponivel as exc:
            return _erro_sheets(exc)
        except Exception as exc:  # pragma: no cover
            return _erro_sheets(f"Falha na importação: {exc}", "sheets_falha", status.HTTP_502_BAD_GATEWAY)


class ControleProdutosSerializer(serializers.Serializer):
    planilha = serializers.CharField()


class PreviaControleProdutosView(_Admin):
    def post(self, request):
        s = ControleProdutosSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            return Response(integracoes.previa_controle_produtos(s.validated_data["planilha"]))
        except integracoes.SheetsIndisponivel as exc:
            return _erro_sheets(exc)
        except Exception as exc:  # pragma: no cover
            return _erro_sheets(f"Não consegui ler a planilha: {exc}", "sheets_falha", status.HTTP_502_BAD_GATEWAY)


class ImportarControleProdutosView(_Admin):
    def post(self, request):
        s = ControleProdutosSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            resumo = integracoes.importar_controle_produtos(s.validated_data["planilha"], request.user)
            return Response(resumo)
        except integracoes.SheetsIndisponivel as exc:
            return _erro_sheets(exc)
        except Exception as exc:  # pragma: no cover
            return _erro_sheets(f"Falha na importação: {exc}", "sheets_falha", status.HTTP_502_BAD_GATEWAY)
