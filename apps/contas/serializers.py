from django.contrib.auth import password_validation
from django.contrib.auth.models import Group
from rest_framework import serializers

from .models import PERFIS, Membro


class GrupoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id", "name"]


class MembroSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(source="nome_exibicao", read_only=True)
    perfis = serializers.ListField(child=serializers.CharField(), read_only=True)
    perfil_principal = serializers.CharField(read_only=True)
    grupos_ids = serializers.PrimaryKeyRelatedField(
        source="groups", queryset=Group.objects.all(), many=True, required=False, write_only=True)
    senha = serializers.CharField(write_only=True, required=False, trim_whitespace=False,
                                  help_text="Obrigatória ao criar; ao editar, só se quiser trocar.")

    class Meta:
        model = Membro
        fields = ["id", "username", "nome", "first_name", "last_name", "email", "cargo", "telefone",
                  "foto", "data_entrada", "data_saida", "observacoes", "is_active", "is_superuser",
                  "last_login", "date_joined", "perfis", "perfil_principal", "grupos_ids", "senha"]
        read_only_fields = ["is_superuser", "last_login", "date_joined", "foto"]

    def validate_username(self, v):
        v = v.strip()
        if not v:
            raise serializers.ValidationError("Informe o usuário.")
        return v

    def validate_senha(self, v):
        password_validation.validate_password(v, self.instance)
        return v

    def validate(self, dados):
        if self.instance is None and not dados.get("senha"):
            raise serializers.ValidationError({"senha": "Defina uma senha inicial."})
        return dados

    def create(self, validated):
        senha = validated.pop("senha")
        grupos = validated.pop("groups", [])
        membro = Membro(**validated)
        membro.set_password(senha)
        membro.save()
        membro.groups.set(grupos)
        return membro

    def update(self, membro, validated):
        senha = validated.pop("senha", None)
        grupos = validated.pop("groups", None)
        for campo, valor in validated.items():
            setattr(membro, campo, valor)
        if senha:
            membro.set_password(senha)
        membro.save()
        if grupos is not None:
            membro.groups.set(grupos)
        return membro


class MeusDadosSerializer(serializers.ModelSerializer):
    """O próprio usuário edita só o básico."""

    class Meta:
        model = Membro
        fields = ["first_name", "last_name", "email", "telefone", "foto"]


class OpcoesMembroSerializer(serializers.Serializer):
    grupos = GrupoSerializer(many=True)
    perfis_ordem = serializers.ListField(default=list(PERFIS))
