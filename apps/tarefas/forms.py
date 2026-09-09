from django import forms

from .models import ComentarioTarefa, Tarefa


class TarefaForm(forms.ModelForm):
    class Meta:
        model = Tarefa
        fields = ["titulo", "descricao", "responsavel", "prazo", "prioridade",
                  "status", "cliente", "pedido", "fornecedor", "anexo"]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 3}),
            "prazo": forms.DateInput(attrs={"type": "date"}),
        }


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = ComentarioTarefa
        fields = ["texto"]
        widgets = {"texto": forms.Textarea(attrs={"rows": 2})}
