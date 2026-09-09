from django import forms

from .models import CustoEvento, Evento, LoteIngresso, ReceitaEvento


class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ["nome", "tipo", "descricao", "data", "horario", "local",
                  "capacidade", "publico_realizado", "staff_cortesias", "status",
                  "publico_alvo", "link_inscricao", "orcamento_previsto",
                  "responsavel", "fornecedores", "observacoes"]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
            "descricao": forms.Textarea(attrs={"rows": 2}),
            "observacoes": forms.Textarea(attrs={"rows": 2}),
            "fornecedores": forms.SelectMultiple(attrs={"size": 4}),
        }


class LoteForm(forms.ModelForm):
    class Meta:
        model = LoteIngresso
        fields = ["nome", "quantidade_prevista", "quantidade_vendida",
                  "valor_unitario", "ordem"]


class CustoForm(forms.ModelForm):
    class Meta:
        model = CustoEvento
        fields = ["tipo", "item", "quantidade", "valor_unitario", "valor_pago",
                  "situacao", "fornecedor", "observacao"]
        widgets = {"observacao": forms.TextInput}


class ReceitaForm(forms.ModelForm):
    class Meta:
        model = ReceitaEvento
        fields = ["origem", "descricao", "valor", "recebido"]
