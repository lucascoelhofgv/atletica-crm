from rest_framework import serializers

from apps.fornecedores.models import Fornecedor
from apps.nucleo.serializers import UsuarioResumoSerializer

from . import services
from .models import CategoriaProduto, MovimentacaoEstoque, Produto


class CategoriaProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaProduto
        fields = ["id", "nome", "descricao", "ativo"]


class FornecedorResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fornecedor
        fields = ["id", "nome", "nome_fantasia"]


class MovimentacaoSerializer(serializers.ModelSerializer):
    tipo_rotulo = serializers.CharField(source="get_tipo_display", read_only=True)
    usuario = UsuarioResumoSerializer(read_only=True)
    produto_nome = serializers.CharField(source="produto.__str__", read_only=True)
    pedido_numero = serializers.CharField(source="pedido.numero", read_only=True, default=None)
    eh_entrada = serializers.BooleanField(read_only=True)

    class Meta:
        model = MovimentacaoEstoque
        fields = ["id", "produto", "produto_nome", "tipo", "tipo_rotulo", "eh_entrada",
                  "quantidade", "saldo_apos", "data", "usuario", "motivo", "pedido",
                  "pedido_numero", "observacao"]
        read_only_fields = ["produto", "saldo_apos", "data", "pedido"]


class MovimentacaoEntradaSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=MovimentacaoEstoque.Tipo.choices)
    quantidade = serializers.IntegerField(min_value=1)
    motivo = serializers.CharField(max_length=160, required=False, allow_blank=True, default="")
    observacao = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class _ProdutoBase(serializers.ModelSerializer):
    categoria = CategoriaProdutoSerializer(read_only=True)
    fornecedor = FornecedorResumoSerializer(read_only=True)
    status_rotulo = serializers.CharField(source="get_status_display", read_only=True)
    situacao = serializers.SerializerMethodField()
    valor_em_estoque = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    margem_estimada = serializers.FloatField(read_only=True, allow_null=True)
    nome_completo = serializers.CharField(source="__str__", read_only=True)

    def get_situacao(self, produto):
        return services.situacao(produto)


class ProdutoListaSerializer(_ProdutoBase):
    class Meta:
        model = Produto
        fields = ["id", "nome", "nome_completo", "tamanho", "cor", "sku", "codigo_interno",
                  "categoria", "fornecedor", "foto", "custo_unitario", "preco_venda",
                  "quantidade_atual", "estoque_minimo", "situacao", "valor_em_estoque",
                  "margem_estimada", "status", "status_rotulo"]


class ProdutoSerializer(_ProdutoBase):
    categoria_id = serializers.PrimaryKeyRelatedField(
        source="categoria", queryset=CategoriaProduto.objects.all(),
        allow_null=True, required=False, write_only=True,
    )
    fornecedor_id = serializers.PrimaryKeyRelatedField(
        source="fornecedor", queryset=Fornecedor.objects.all(),
        allow_null=True, required=False, write_only=True,
    )
    criado_por = UsuarioResumoSerializer(read_only=True)
    movimentacoes_recentes = serializers.SerializerMethodField()

    class Meta:
        model = Produto
        fields = [
            "id", "nome", "nome_completo", "codigo_interno", "sku", "categoria", "categoria_id",
            "descricao", "foto", "tamanho", "cor", "marca", "fornecedor", "fornecedor_id",
            "custo_unitario", "preco_venda", "quantidade_atual", "estoque_minimo",
            "estoque_maximo", "localizacao", "status", "status_rotulo", "observacoes",
            "criado_em", "criado_por", "situacao", "valor_em_estoque", "margem_estimada",
            "movimentacoes_recentes",
        ]
        # O saldo só muda por movimentação, nunca por edição direta.
        read_only_fields = ["quantidade_atual", "criado_em"]

    def get_movimentacoes_recentes(self, produto):
        qs = produto.movimentacoes.select_related("usuario", "pedido")[:30]
        return MovimentacaoSerializer(qs, many=True).data

    def validate_nome(self, valor):
        valor = valor.strip()
        if not valor:
            raise serializers.ValidationError("Informe o nome.")
        return valor

    def validate(self, dados):
        erros = {}
        custo = dados.get("custo_unitario", getattr(self.instance, "custo_unitario", 0))
        preco = dados.get("preco_venda", getattr(self.instance, "preco_venda", 0))
        if custo is not None and custo < 0:
            erros["custo_unitario"] = "Não pode ser negativo."
        if preco is not None and preco < 0:
            erros["preco_venda"] = "Não pode ser negativo."
        minimo = dados.get("estoque_minimo", getattr(self.instance, "estoque_minimo", 0))
        maximo = dados.get("estoque_maximo", getattr(self.instance, "estoque_maximo", None))
        if maximo is not None and minimo is not None and maximo < minimo:
            erros["estoque_maximo"] = "Deve ser maior que o mínimo."
        if erros:
            raise serializers.ValidationError(erros)
        return dados


class OpcoesProdutoSerializer(serializers.Serializer):
    categorias = CategoriaProdutoSerializer(many=True)
    fornecedores = FornecedorResumoSerializer(many=True)
    status = serializers.ListField()
    tipos_movimentacao = serializers.ListField()
