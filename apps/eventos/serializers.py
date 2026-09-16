from rest_framework import serializers

from apps.contas.models import Membro
from apps.fornecedores.models import Fornecedor
from apps.nucleo.serializers import UsuarioResumoSerializer

from . import services
from .models import CustoEvento, Evento, LoteIngresso, ReceitaEvento


class FornecedorMiniSerializer(serializers.ModelSerializer):
    nome_exibicao = serializers.CharField(source="__str__", read_only=True)

    class Meta:
        model = Fornecedor
        fields = ["id", "nome", "nome_fantasia", "nome_exibicao"]


class LoteSerializer(serializers.ModelSerializer):
    total_previsto = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_vendido = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = LoteIngresso
        fields = ["id", "nome", "quantidade_prevista", "quantidade_vendida", "valor_unitario",
                  "ordem", "total_previsto", "total_vendido"]

    def validate(self, d):
        prevista = d.get("quantidade_prevista", getattr(self.instance, "quantidade_prevista", 0))
        vendida = d.get("quantidade_vendida", getattr(self.instance, "quantidade_vendida", 0))
        if vendida > prevista and prevista:
            raise serializers.ValidationError({"quantidade_vendida": "Maior que a quantidade prevista."})
        return d


class CustoSerializer(serializers.ModelSerializer):
    tipo_rotulo = serializers.CharField(source="get_tipo_display", read_only=True)
    situacao_rotulo = serializers.CharField(source="get_situacao_display", read_only=True)
    fornecedor = FornecedorMiniSerializer(read_only=True)
    fornecedor_id = serializers.PrimaryKeyRelatedField(
        source="fornecedor", queryset=Fornecedor.objects.all(), allow_null=True, required=False, write_only=True)
    valor_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CustoEvento
        fields = ["id", "tipo", "tipo_rotulo", "item", "quantidade", "valor_unitario", "valor_pago",
                  "situacao", "situacao_rotulo", "fornecedor", "fornecedor_id", "observacao", "valor_total"]


class ReceitaSerializer(serializers.ModelSerializer):
    origem_rotulo = serializers.CharField(source="get_origem_display", read_only=True)

    class Meta:
        model = ReceitaEvento
        fields = ["id", "origem", "origem_rotulo", "descricao", "valor", "recebido"]


class _Base(serializers.ModelSerializer):
    tipo_rotulo = serializers.CharField(source="get_tipo_display", read_only=True)
    status_rotulo = serializers.CharField(source="get_status_display", read_only=True)
    responsavel = UsuarioResumoSerializer(read_only=True)
    financeiro = serializers.SerializerMethodField()

    def get_financeiro(self, e):
        return services.resumo_financeiro(e)


class EventoListaSerializer(_Base):
    class Meta:
        model = Evento
        fields = ["id", "nome", "tipo", "tipo_rotulo", "data", "horario", "local", "status", "status_rotulo",
                  "capacidade", "responsavel", "financeiro"]


class EventoSerializer(_Base):
    responsavel_id = serializers.PrimaryKeyRelatedField(
        source="responsavel", queryset=Membro.objects.filter(is_active=True),
        allow_null=True, required=False, write_only=True)
    fornecedores = FornecedorMiniSerializer(many=True, read_only=True)
    fornecedores_ids = serializers.PrimaryKeyRelatedField(
        source="fornecedores", queryset=Fornecedor.objects.all(), many=True, required=False, write_only=True)
    criado_por = UsuarioResumoSerializer(read_only=True)
    lotes = LoteSerializer(many=True, read_only=True)
    custos = CustoSerializer(many=True, read_only=True)
    receitas = ReceitaSerializer(many=True, read_only=True)

    class Meta:
        model = Evento
        fields = ["id", "nome", "tipo", "tipo_rotulo", "descricao", "data", "horario", "local",
                  "capacidade", "publico_realizado", "staff_cortesias", "status", "status_rotulo",
                  "publico_alvo", "link_inscricao", "orcamento_previsto", "responsavel", "responsavel_id",
                  "fornecedores", "fornecedores_ids", "observacoes", "criado_em", "criado_por",
                  "financeiro", "lotes", "custos", "receitas"]
        read_only_fields = ["criado_em"]

    def validate_nome(self, v):
        v = v.strip()
        if not v:
            raise serializers.ValidationError("Informe o nome.")
        return v


class OpcoesEventoSerializer(serializers.Serializer):
    tipos = serializers.ListField()
    status = serializers.ListField()
    tipos_custo = serializers.ListField()
    situacoes_custo = serializers.ListField()
    origens_receita = serializers.ListField()
    membros = UsuarioResumoSerializer(many=True)
    fornecedores = FornecedorMiniSerializer(many=True)
