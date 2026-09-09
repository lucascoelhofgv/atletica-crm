"""Modelos do núcleo: identidade visual (white-label), registro de atividades
e histórico de acessos."""

from django.conf import settings
from django.db import models


class Configuracao(models.Model):
    """Configuração única da instância (identidade visual e dados institucionais).

    Sempre usada via ``Configuracao.carregar()`` — existe um único registro (pk=1).
    """

    nome_organizacao = models.CharField(
        "nome da organização", max_length=120, default="Atlética FGV Rio"
    )
    titulo_app = models.CharField(
        "título da aplicação", max_length=120, default="CRM Atlética"
    )
    sobre = models.TextField("informações institucionais", blank=True)

    logo = models.ImageField("logo", upload_to="identidade/", blank=True, null=True)
    favicon = models.ImageField(
        "favicon", upload_to="identidade/", blank=True, null=True
    )
    banner = models.ImageField(
        "imagem de capa / banner", upload_to="identidade/", blank=True, null=True
    )

    cor_primaria = models.CharField("cor primária", max_length=7, default="#1B2A4A")
    cor_secundaria = models.CharField(
        "cor secundária", max_length=7, default="#F4B400"
    )

    email_contato = models.EmailField("e-mail de contato", blank=True)
    telefone_contato = models.CharField("telefone de contato", max_length=40, blank=True)
    site = models.URLField("site", blank=True)
    instagram = models.CharField("Instagram", max_length=120, blank=True)
    endereco = models.CharField("endereço", max_length=255, blank=True)

    modo_escuro_disponivel = models.BooleanField(
        "disponibilizar modo escuro", default=False
    )

    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "configuração"
        verbose_name_plural = "configurações"

    def __str__(self):
        return self.nome_organizacao

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def carregar(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class RegistroAtividade(models.Model):
    """Linha do tempo de atividades exibida no dashboard e nas telas de detalhe."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="atividades",
        verbose_name="usuário",
    )
    verbo = models.CharField("ação", max_length=40)
    alvo = models.CharField("registro afetado", max_length=160, blank=True)
    descricao = models.CharField("descrição", max_length=255, blank=True)
    url = models.CharField("link", max_length=255, blank=True)
    criado_em = models.DateTimeField("data e hora", auto_now_add=True)

    class Meta:
        verbose_name = "registro de atividade"
        verbose_name_plural = "registros de atividade"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.usuario} {self.verbo} {self.alvo}".strip()


class LogAcesso(models.Model):
    """Histórico de acessos por usuário (seção 3 do escopo)."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="acessos",
        verbose_name="usuário",
    )
    momento = models.DateTimeField("momento", auto_now_add=True)
    ip = models.GenericIPAddressField("endereço IP", null=True, blank=True)
    agente = models.CharField("navegador / dispositivo", max_length=255, blank=True)
    sucesso = models.BooleanField("acesso bem-sucedido", default=True)

    class Meta:
        verbose_name = "log de acesso"
        verbose_name_plural = "logs de acesso"
        ordering = ["-momento"]

    def __str__(self):
        estado = "ok" if self.sucesso else "falha"
        return f"{self.usuario} — {self.momento:%d/%m/%Y %H:%M} ({estado})"


def registrar_atividade(usuario, verbo, alvo="", descricao="", url=""):
    """Atalho para gravar uma linha em RegistroAtividade sem quebrar a request
    caso algo dê errado."""
    try:
        RegistroAtividade.objects.create(
            usuario=usuario if getattr(usuario, "is_authenticated", False) else None,
            verbo=verbo,
            alvo=str(alvo)[:160],
            descricao=str(descricao)[:255],
            url=url[:255],
        )
    except Exception:  # pragma: no cover - telemetria não pode derrubar a tela
        pass
