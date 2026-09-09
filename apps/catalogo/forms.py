from django import forms

from .models import MovimentacaoEstoque, Produto


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        exclude = ["criado_em", "criado_por", "quantidade_atual"]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 2}),
            "observacoes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["_saldo_atual"] = forms.IntegerField(
                label="Saldo atual (ajuste pela tela de movimentação)",
                initial=self.instance.quantidade_atual,
                required=False,
                disabled=True,
            )


class MovimentacaoForm(forms.ModelForm):
    class Meta:
        model = MovimentacaoEstoque
        fields = ["tipo", "quantidade", "motivo", "observacao"]
        widgets = {"observacao": forms.TextInput}
