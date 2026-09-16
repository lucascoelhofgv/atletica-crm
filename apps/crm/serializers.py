from rest_framework import serializers

from apps.nucleo.serializers import UsuarioResumoSerializer

from .models import CategoriaCliente, Cliente, Interacao, Tag


class CategoriaClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaCliente
        fields = ["id", "nome", "cor", "ativo"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "nome", "cor"]


class InteracaoSerializer(serializers.ModelSerializer):
    tipo_rotulo = serializers.CharField(source="get_tipo_display", read_only=True)
    registrado_por = UsuarioResumoSerializer(read_only=True)

    class Meta:
        model = Interacao
        fields = ["id", "tipo", "tipo_rotulo", "resumo", "detalhe", "data",
                  "registrado_por", "criado_em"]
        read_only_fields = ["criado_em"]


class ClienteListaSerializer(serializers.ModelSerializer):
    """Linha da listagem: só o que a tabela mostra."""

    categoria = CategoriaClienteSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    relacionamento_rotulo = serializers.CharField(source="get_relacionamento_display", read_only=True)
    vinculo_rotulo = serializers.CharField(source="get_vinculo_display", read_only=True)
    qtd_pedidos = serializers.IntegerField(read_only=True, default=0)
    total_gasto = serializers.DecimalField(
        source="total_gasto_calc", max_digits=12, decimal_places=2, read_only=True, default=0
    )

    class Meta:
        model = Cliente
        fields = [
            "id", "nome", "nome_social", "email", "telefone", "whatsapp", "curso", "periodo",
            "membro_fgv", "vinculo", "vinculo_rotulo", "categoria", "tags",
            "relacionamento", "relacionamento_rotulo", "qtd_pedidos", "total_gasto", "criado_em",
        ]


class PedidoResumoSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    numero = serializers.CharField()
    status = serializers.CharField()
    status_rotulo = serializers.CharField(source="get_status_display")
    valor_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    data_compra = serializers.DateField()
    url = serializers.CharField(source="get_absolute_url")


class ClienteSerializer(serializers.ModelSerializer):
    """Detalhe e escrita. Categoria e tags entram por id e saem aninhadas."""

    categoria = CategoriaClienteSerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(
        source="categoria", queryset=CategoriaCliente.objects.all(),
        allow_null=True, required=False, write_only=True,
    )
    tags = TagSerializer(many=True, read_only=True)
    tags_ids = serializers.PrimaryKeyRelatedField(
        source="tags", queryset=Tag.objects.all(), many=True, required=False, write_only=True,
    )
    relacionamento_rotulo = serializers.CharField(source="get_relacionamento_display", read_only=True)
    vinculo_rotulo = serializers.CharField(source="get_vinculo_display", read_only=True)
    criado_por = UsuarioResumoSerializer(read_only=True)
    qtd_pedidos = serializers.IntegerField(read_only=True, default=0)
    total_gasto = serializers.DecimalField(
        source="total_gasto_calc", max_digits=12, decimal_places=2, read_only=True, default=0
    )
    pedidos_recentes = serializers.SerializerMethodField()
    interacoes = InteracaoSerializer(many=True, read_only=True)

    class Meta:
        model = Cliente
        fields = [
            "id", "nome", "nome_social", "cpf", "data_nascimento",
            "email", "telefone", "whatsapp", "cidade", "endereco",
            "membro_fgv", "vinculo", "vinculo_rotulo", "curso", "periodo", "campus", "turma",
            "categoria", "categoria_id", "tags", "tags_ids", "origem",
            "relacionamento", "relacionamento_rotulo", "aceita_comunicacoes", "observacoes",
            "criado_em", "atualizado_em", "criado_por",
            "qtd_pedidos", "total_gasto", "pedidos_recentes", "interacoes",
        ]
        read_only_fields = ["criado_em", "atualizado_em"]

    def get_pedidos_recentes(self, cliente):
        pedidos = cliente.pedidos.order_by("-data_compra", "-id")[:10]
        return PedidoResumoSerializer(pedidos, many=True).data

    def validate_nome(self, valor):
        valor = valor.strip()
        if not valor:
            raise serializers.ValidationError("Informe o nome.")
        return valor


class OpcoesClienteSerializer(serializers.Serializer):
    """Listas para os formulários e filtros (categorias, tags, choices)."""

    categorias = CategoriaClienteSerializer(many=True)
    tags = TagSerializer(many=True)
    vinculos = serializers.ListField()
    relacionamentos = serializers.ListField()
    tipos_interacao = serializers.ListField()
