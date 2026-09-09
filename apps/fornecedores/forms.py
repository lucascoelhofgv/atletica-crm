from django import forms

from .models import AvaliacaoFornecedor, Fornecedor


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        exclude = ["criado_em", "criado_por"]
        widgets = {
            "produtos_servicos": forms.Textarea(attrs={"rows": 2}),
            "condicoes_comerciais": forms.Textarea(attrs={"rows": 2}),
            "observacoes": forms.Textarea(attrs={"rows": 2}),
        }


class AvaliacaoForm(forms.ModelForm):
    class Meta:
        model = AvaliacaoFornecedor
        fields = ["preco", "qualidade", "prazo", "atendimento", "confiabilidade",
                  "comentario"]
        widgets = {"comentario": forms.Textarea(attrs={"rows": 2})}
