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
