from django import forms
from django.forms import inlineformset_factory

from apps.catalogo.models import Produto

from .models import ItemPedido, Pagamento, Pedido


class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ["cliente", "status", "forma_pagamento", "status_pagamento",
                  "desconto", "taxa", "data_compra", "data_entrega",
                  "local_retirada", "responsavel", "observacoes", "comprovante"]
        widgets = {
            "data_compra": forms.DateInput(attrs={"type": "date"}),
            "data_entrega": forms.DateInput(attrs={"type": "date"}),
            "observacoes": forms.Textarea(attrs={"rows": 2}),
        }


class ItemPedidoForm(forms.ModelForm):
    class Meta:
        model = ItemPedido
        fields = ["produto", "quantidade", "preco_unitario", "desconto_item"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["produto"].queryset = Produto.objects.filter(
            status=Produto.Status.ATIVO
        )
        # linhas extras aparecem em branco (sem "1" pré-preenchido) para que
        # o formset as trate como vazias quando não usadas
        self.fields["quantidade"].initial = None

    def has_changed(self):
        # uma linha sem produto escolhido é considerada vazia e ignorada
        if not self.add_prefix("produto") in (self.data or {}):
            return super().has_changed()
        if not (self.data.get(self.add_prefix("produto")) or "").strip():
            return False
        return super().has_changed()


ItemPedidoFormSet = inlineformset_factory(
    Pedido, ItemPedido, form=ItemPedidoForm, extra=3, can_delete=True
)


class PagamentoForm(forms.ModelForm):
    class Meta:
        model = Pagamento
        fields = ["valor", "forma", "data", "observacao"]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
            "observacao": forms.TextInput,
        }
