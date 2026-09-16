from rest_framework import serializers

from apps.contas.models import Membro
from apps.crm.models import Cliente
from apps.fornecedores.models import Fornecedor
from apps.nucleo.serializers import UsuarioResumoSerializer
from apps.vendas.models import Pedido

from .models import ComentarioTarefa, Tarefa


class ComentarioSerializer(serializers.ModelSerializer):
    autor = UsuarioResumoSerializer(read_only=True)

    class Meta:
        model = ComentarioTarefa
        fields = ["id", "texto", "autor", "criado_em"]
        read_only_fields = ["criado_em"]


class _Vinculo(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    nome = serializers.CharField(source="__str__", read_only=True)


class TarefaSerializer(serializers.ModelSerializer):
    responsavel = UsuarioResumoSerializer(read_only=True)
    criador = UsuarioResumoSerializer(read_only=True)
    cliente = _Vinculo(read_only=True)
    pedido = _Vinculo(read_only=True)
    fornecedor = _Vinculo(read_only=True)
    responsavel_id = serializers.PrimaryKeyRelatedField(
        source="responsavel", queryset=Membro.objects.filter(is_active=True),
        allow_null=True, required=False, write_only=True)
    cliente_id = serializers.PrimaryKeyRelatedField(
        source="cliente", queryset=Cliente.objects.all(), allow_null=True, required=False, write_only=True)
    pedido_id = serializers.PrimaryKeyRelatedField(
        source="pedido", queryset=Pedido.objects.all(), allow_null=True, required=False, write_only=True)
    fornecedor_id = serializers.PrimaryKeyRelatedField(
        source="fornecedor", queryset=Fornecedor.objects.all(), allow_null=True, required=False, write_only=True)
    prioridade_rotulo = serializers.CharField(source="get_prioridade_display", read_only=True)
    status_rotulo = serializers.CharField(source="get_status_display", read_only=True)
    atrasada = serializers.BooleanField(read_only=True)
    comentarios = ComentarioSerializer(many=True, read_only=True)
    qtd_comentarios = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Tarefa
        fields = ["id", "titulo", "descricao", "responsavel", "responsavel_id", "criador", "prazo",
                  "prioridade", "prioridade_rotulo", "status", "status_rotulo", "atrasada",
                  "cliente", "cliente_id", "pedido", "pedido_id", "fornecedor", "fornecedor_id",
                  "anexo", "criado_em", "atualizado_em", "concluida_em", "comentarios", "qtd_comentarios"]
        read_only_fields = ["anexo", "criado_em", "atualizado_em", "concluida_em"]

    def validate_titulo(self, v):
        v = v.strip()
        if not v:
            raise serializers.ValidationError("Informe o título.")
        return v


class TarefaCartaoSerializer(TarefaSerializer):
    """Versão leve para lista e quadro (sem comentários)."""

    class Meta(TarefaSerializer.Meta):
        fields = [f for f in TarefaSerializer.Meta.fields if f != "comentarios"]


class OpcoesTarefaSerializer(serializers.Serializer):
    status = serializers.ListField()
    prioridades = serializers.ListField()
    membros = UsuarioResumoSerializer(many=True)
