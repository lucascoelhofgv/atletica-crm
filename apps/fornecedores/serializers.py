from rest_framework import serializers

from apps.nucleo.serializers import UsuarioResumoSerializer

from .models import AvaliacaoFornecedor, Fornecedor


class AvaliacaoSerializer(serializers.ModelSerializer):
    autor = UsuarioResumoSerializer(read_only=True)
    media = serializers.FloatField(read_only=True)

    class Meta:
        model = AvaliacaoFornecedor
        fields = ["id", "preco", "qualidade", "prazo", "atendimento", "confiabilidade",
                  "comentario", "media", "autor", "criado_em"]
        read_only_fields = ["criado_em"]


class _Base(serializers.ModelSerializer):
    nome_exibicao = serializers.CharField(source="__str__", read_only=True)
    categoria_rotulo = serializers.CharField(source="get_categoria_display", read_only=True)
    status_rotulo = serializers.CharField(source="get_status_display", read_only=True)
    qtd_produtos = serializers.IntegerField(read_only=True, default=0)
    qtd_avaliacoes = serializers.IntegerField(read_only=True, default=0)
    nota_media = serializers.FloatField(source="nota_media_calc", read_only=True, allow_null=True, default=None)


class FornecedorListaSerializer(_Base):
    class Meta:
        model = Fornecedor
        fields = ["id", "nome", "nome_fantasia", "nome_exibicao", "categoria", "categoria_rotulo",
                  "contato_nome", "email", "whatsapp", "telefone", "status", "status_rotulo",
                  "qtd_produtos", "qtd_avaliacoes", "nota_media", "prazo_medio_entrega"]


class FornecedorSerializer(_Base):
    criado_por = UsuarioResumoSerializer(read_only=True)
    avaliacoes = AvaliacaoSerializer(many=True, read_only=True)
    produtos = serializers.SerializerMethodField()

    class Meta:
        model = Fornecedor
        fields = ["id", "nome", "nome_fantasia", "nome_exibicao", "documento", "contato_nome",
                  "email", "telefone", "whatsapp", "endereco", "categoria", "categoria_rotulo",
                  "produtos_servicos", "condicoes_comerciais", "prazo_medio_entrega", "status",
                  "status_rotulo", "contrato", "observacoes", "criado_em", "criado_por",
                  "qtd_produtos", "qtd_avaliacoes", "nota_media", "avaliacoes", "produtos"]
        read_only_fields = ["criado_em", "contrato"]

    def get_produtos(self, f):
        return [
            {"id": p.id, "nome": str(p), "quantidade_atual": p.quantidade_atual, "preco_venda": p.preco_venda}
            for p in f.produtos.order_by("nome")[:20]
        ]

    def validate_nome(self, valor):
        valor = valor.strip()
        if not valor:
            raise serializers.ValidationError("Informe o nome.")
        return valor


class OpcoesFornecedorSerializer(serializers.Serializer):
    categorias = serializers.ListField()
    status = serializers.ListField()
