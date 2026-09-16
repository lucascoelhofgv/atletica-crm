from decimal import Decimal

from rest_framework import serializers

from apps.catalogo.models import Produto
from apps.contas.models import Membro
from apps.crm.models import Cliente
from apps.nucleo.serializers import UsuarioResumoSerializer

from .models import ItemPedido, Pagamento, Pedido


class ClienteResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ["id", "nome", "nome_social", "email", "whatsapp", "telefone"]


class ProdutoItemSerializer(serializers.ModelSerializer):
    nome_completo = serializers.CharField(source="__str__", read_only=True)

    class Meta:
        model = Produto
        fields = ["id", "nome", "nome_completo", "tamanho", "sku", "preco_venda",
                  "quantidade_atual", "status", "foto"]


class ItemPedidoSerializer(serializers.ModelSerializer):
    produto = ProdutoItemSerializer(read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = ItemPedido
        fields = ["id", "produto", "quantidade", "preco_unitario", "desconto_item", "total"]


class ItemEntradaSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    produto = serializers.PrimaryKeyRelatedField(queryset=Produto.objects.all())
    quantidade = serializers.IntegerField(min_value=1)
    preco_unitario = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0"),
                                              required=False, allow_null=True)
    desconto_item = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0"),
                                             required=False, default=Decimal("0"))


class PagamentoSerializer(serializers.ModelSerializer):
    forma_rotulo = serializers.CharField(source="get_forma_display", read_only=True)
    registrado_por = UsuarioResumoSerializer(read_only=True)

    class Meta:
        model = Pagamento
        fields = ["id", "valor", "forma", "forma_rotulo", "data", "observacao",
                  "registrado_por", "criado_em"]
        read_only_fields = ["criado_em"]

    def validate_valor(self, v):
        if v <= 0:
            raise serializers.ValidationError("Informe um valor maior que zero.")
        return v


class _PedidoBase(serializers.ModelSerializer):
    cliente = ClienteResumoSerializer(read_only=True)
    responsavel = UsuarioResumoSerializer(read_only=True)
    status_rotulo = serializers.CharField(source="get_status_display", read_only=True)
    status_pagamento_rotulo = serializers.CharField(source="get_status_pagamento_display", read_only=True)
    forma_pagamento_rotulo = serializers.CharField(source="get_forma_pagamento_display", read_only=True)
    total_pago = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    saldo_devedor = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)


class PedidoListaSerializer(_PedidoBase):
    qtd_itens = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Pedido
        fields = ["id", "numero", "cliente", "status", "status_rotulo", "status_pagamento",
                  "status_pagamento_rotulo", "forma_pagamento", "forma_pagamento_rotulo",
                  "valor_total", "total_pago", "saldo_devedor", "data_compra", "data_entrega",
                  "responsavel", "qtd_itens", "estoque_baixado", "criado_em"]


class PedidoSerializer(_PedidoBase):
    itens = ItemPedidoSerializer(many=True, read_only=True)
    pagamentos = PagamentoSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    criado_por = UsuarioResumoSerializer(read_only=True)
    faltas = serializers.SerializerMethodField()
    url_recibo = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = ["id", "numero", "cliente", "status", "status_rotulo", "status_pagamento",
                  "status_pagamento_rotulo", "forma_pagamento", "forma_pagamento_rotulo",
                  "desconto", "taxa", "subtotal", "valor_total", "total_pago", "saldo_devedor",
                  "data_compra", "data_entrega", "local_retirada", "observacoes", "comprovante",
                  "estoque_baixado", "responsavel", "criado_por", "criado_em", "atualizado_em",
                  "itens", "pagamentos", "faltas", "url_recibo"]

    def get_faltas(self, pedido):
        if pedido.estoque_baixado:
            return []
        return [
            {"produto_id": p.id, "produto": str(p), "necessario": n, "disponivel": d}
            for p, n, d in pedido.itens_sem_estoque()
        ]

    def get_url_recibo(self, pedido):
        return f"/pedidos/{pedido.pk}/recibo/"


class PedidoEntradaSerializer(serializers.Serializer):
    """Corpo de POST/PATCH. ``itens`` é a lista completa desejada."""

    cliente = serializers.PrimaryKeyRelatedField(queryset=Cliente.objects.all())
    status = serializers.ChoiceField(choices=Pedido.Status.choices, default=Pedido.Status.RASCUNHO)
    forma_pagamento = serializers.ChoiceField(choices=Pedido.FormaPagamento.choices, required=False,
                                              allow_blank=True)
    status_pagamento = serializers.ChoiceField(choices=Pedido.StatusPagamento.choices, required=False)
    desconto = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0"),
                                        required=False, default=Decimal("0"))
    taxa = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0"),
                                    required=False, default=Decimal("0"))
    data_compra = serializers.DateField(required=False)
    data_entrega = serializers.DateField(required=False, allow_null=True)
    local_retirada = serializers.CharField(max_length=160, required=False, allow_blank=True, default="")
    responsavel = serializers.PrimaryKeyRelatedField(queryset=Membro.objects.filter(is_active=True),
                                                     required=False, allow_null=True)
    observacoes = serializers.CharField(required=False, allow_blank=True, default="")
    itens = ItemEntradaSerializer(many=True, required=False)

    def __init__(self, *args, parcial=False, **kwargs):
        super().__init__(*args, **kwargs)
        if parcial:
            for campo in self.fields.values():
                campo.required = False
                campo.default = serializers.empty

    def validate_itens(self, itens):
        if itens is not None and len(itens) == 0 and not self.partial:
            pass  # rascunho pode não ter itens
        return itens


class OpcoesPedidoSerializer(serializers.Serializer):
    status = serializers.ListField()
    formas_pagamento = serializers.ListField()
    status_pagamento = serializers.ListField()
    membros = UsuarioResumoSerializer(many=True)
