from django import forms

from .models import Cliente, Interacao


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        exclude = ["criado_em", "atualizado_em", "criado_por"]
        widgets = {
            "data_nascimento": forms.DateInput(attrs={"type": "date"}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
            "tags": forms.CheckboxSelectMultiple,
            "endereco": forms.TextInput,
        }


class InteracaoForm(forms.ModelForm):
    class Meta:
        model = Interacao
        fields = ["tipo", "resumo", "detalhe", "data"]
        widgets = {
            "data": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "detalhe": forms.Textarea(attrs={"rows": 3}),
        }


class ImportarClientesForm(forms.Form):
    arquivo = forms.FileField(
        label="Arquivo CSV",
        help_text="Colunas aceitas: nome, email, telefone, whatsapp, curso, "
        "periodo, campus, cidade, categoria, origem, observacoes.",
    )
