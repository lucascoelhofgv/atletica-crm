from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import Group

from .models import Membro


CAMPOS_PERFIL = ("first_name", "last_name", "email", "cargo", "telefone",
                 "foto", "data_entrada", "data_saida", "observacoes")


class MembroCreateForm(UserCreationForm):
    grupos = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Perfis de acesso",
    )

    class Meta:
        model = Membro
        fields = ("username", "first_name", "last_name", "email", "cargo",
                  "telefone", "data_entrada")

    def save(self, commit=True):
        membro = super().save(commit)
        if commit:
            membro.groups.set(self.cleaned_data["grupos"])
        return membro


class MembroUpdateForm(forms.ModelForm):
    grupos = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Perfis de acesso",
    )

    class Meta:
        model = Membro
        fields = ("username", *CAMPOS_PERFIL, "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["grupos"].initial = self.instance.groups.all()

    def save(self, commit=True):
        membro = super().save(commit)
        if commit:
            membro.groups.set(self.cleaned_data["grupos"])
        return membro


class MeusDadosForm(forms.ModelForm):
    class Meta:
        model = Membro
        fields = ("first_name", "last_name", "email", "telefone", "foto")
