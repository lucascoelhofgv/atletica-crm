"""``/api/integracoes/*`` (só administrador)."""

from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import SomenteAdmin

from .models import FontePlanilha, registrar_atividade
from .services import integracoes
from .sheets import extrair_id_planilha


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


# --------------------------------------------------------------------------- #
# Fontes de planilha (cadastro + botão "Sincronizar agora")
# --------------------------------------------------------------------------- #
class FontePlanilhaSerializer(serializers.ModelSerializer):
    destino_rotulo = serializers.CharField(source="get_destino_display", read_only=True)
    criado_por_nome = serializers.SerializerMethodField()

    class Meta:
        model = FontePlanilha
        fields = [
            "id", "nome", "planilha", "aba", "destino", "destino_rotulo", "modo", "ativa",
            "ultima_sincronizacao", "ultimo_resultado", "ultimo_erro",
            "criado_em", "criado_por_nome",
        ]
        read_only_fields = ["ultima_sincronizacao", "ultimo_resultado", "ultimo_erro", "criado_em"]

    def get_criado_por_nome(self, obj):
        u = obj.criado_por
        return (getattr(u, "nome_exibicao", "") or u.get_username()) if u else ""

    def validate_planilha(self, valor):
        if not extrair_id_planilha(valor):
            raise serializers.ValidationError("Cole a URL ou o ID da planilha.")
        return valor.strip()


class FontePlanilhaViewSet(viewsets.ModelViewSet):
    """``/api/integracoes/fontes/``: as planilhas que alimentam o CRM."""

    permission_classes = [IsAuthenticated, SomenteAdmin]
    serializer_class = FontePlanilhaSerializer
    queryset = FontePlanilha.objects.select_related("criado_por")
    pagination_class = None
    filterset_fields = ["destino", "ativa"]

    def perform_create(self, serializer):
        fonte = serializer.save(criado_por=self.request.user)
        registrar_atividade(self.request.user, "cadastrou fonte de planilha", fonte.nome)

    def _rodar(self, request, simular):
        fonte = self.get_object()
        try:
            resultado = integracoes.sincronizar_fonte(fonte, usuario=request.user, simular=simular)
        except ValueError as exc:
            return _erro_sheets(exc, "validacao", status.HTTP_400_BAD_REQUEST)
        except integracoes.SheetsIndisponivel as exc:
            return _erro_sheets(exc)
        except Exception as exc:  # pragma: no cover - erro remoto do Google
            return _erro_sheets(f"Falha ao sincronizar: {exc}", "sheets_falha", status.HTTP_502_BAD_GATEWAY)
        fonte.refresh_from_db()
        return Response({**resultado, "fonte": self.get_serializer(fonte).data})

    @action(detail=False, methods=["get"])
    def opcoes(self, request):
        return Response({
            "destinos": [{"valor": v, "rotulo": r} for v, r in FontePlanilha.Destino.choices],
            "modos": [{"valor": v, "rotulo": r} for v, r in FontePlanilha.Modo.choices],
            "conta_servico": integracoes.email_conta_servico(),
        })

    @action(detail=True, methods=["post"])
    def sincronizar(self, request, pk=None):
        return self._rodar(request, simular=False)

    @action(detail=True, methods=["post"])
    def simular(self, request, pk=None):
        return self._rodar(request, simular=True)
