from django import forms

from .importadores import IMPORTADORES
from .models import Configuracao


class ConfiguracaoForm(forms.ModelForm):
    class Meta:
        model = Configuracao
        exclude = ["atualizado_em"]
        widgets = {
            "cor_primaria": forms.TextInput(attrs={"type": "color"}),
            "cor_secundaria": forms.TextInput(attrs={"type": "color"}),
            "sobre": forms.Textarea(attrs={"rows": 3}),
        }


class ImportarPlanilhaForm(forms.Form):
    planilha = forms.CharField(
        label="URL ou ID da planilha de origem",
        help_text="Cole a URL do Google Sheets ou só o ID (trecho entre /d/ e /edit).",
    )
    aba = forms.CharField(
        label="Nome da aba", required=False,
        help_text="Deixe em branco para usar a primeira aba.",
    )
    destino = forms.ChoiceField(
        label="Importar como",
        choices=[(k, v[0]) for k, v in IMPORTADORES.items()],
    )
    modo = forms.ChoiceField(
        label="Modo",
        choices=[
            ("criar_atualizar", "Criar novos e completar dados dos existentes"),
            ("somente_criar", "Só criar novos (ignorar quem já existe)"),
        ],
        initial="criar_atualizar",
    )
    previa = forms.BooleanField(
        label="Só pré-visualizar (não grava nada)", required=False, initial=True,
    )
