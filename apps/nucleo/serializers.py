from rest_framework import serializers

from apps.nucleo.permissoes import mapa_permissoes

from .models import Configuracao, LogAcesso, RegistroAtividade


class ConfiguracaoSerializer(serializers.ModelSerializer):
    """Identidade visual e dados institucionais (white-label). A leitura é
    pública porque a tela de login precisa do logo e das cores."""

    class Meta:
        model = Configuracao
        fields = [
            "nome_organizacao", "titulo_app", "sobre",
            "logo", "favicon", "banner",
            "cor_primaria", "cor_secundaria", "modo_escuro_disponivel",
            "email_contato", "telefone_contato", "site", "instagram", "endereco",
            "atualizado_em",
        ]
        read_only_fields = ["atualizado_em"]


class MembroAtualSerializer(serializers.Serializer):
    """Usuário logado, como o frontend precisa ver."""

    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    nome = serializers.CharField(source="nome_exibicao", read_only=True)
    email = serializers.EmailField(read_only=True)
    cargo = serializers.CharField(read_only=True)
    foto = serializers.ImageField(read_only=True)
    perfis = serializers.ListField(child=serializers.CharField(), read_only=True)
    perfil_principal = serializers.CharField(read_only=True)
    eh_admin = serializers.BooleanField(read_only=True)
    somente_leitura = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    permissoes = serializers.SerializerMethodField()

    def get_permissoes(self, membro):
        return mapa_permissoes(membro)


class UsuarioResumoSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    nome = serializers.CharField(source="nome_exibicao", read_only=True)


class RegistroAtividadeSerializer(serializers.ModelSerializer):
    usuario = UsuarioResumoSerializer(read_only=True)

    class Meta:
        model = RegistroAtividade
        fields = ["id", "usuario", "verbo", "alvo", "descricao", "url", "criado_em"]


class LogAcessoSerializer(serializers.ModelSerializer):
    usuario = UsuarioResumoSerializer(read_only=True)

    class Meta:
        model = LogAcesso
        fields = ["id", "usuario", "momento", "ip", "agente", "sucesso"]
