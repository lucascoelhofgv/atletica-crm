"""Fornecedores e parceiros da Atlética."""

from django.conf import settings
from django.db import models
from django.urls import reverse
from simple_history.models import HistoricalRecords


class Fornecedor(models.Model):
    class Categoria(models.TextChoices):
        CONFECCAO = "confeccao", "Confecção"
        BEBIDAS = "bebidas", "Bebidas"
        ALIMENTACAO = "alimentacao", "Alimentação"
        TRANSPORTE = "transporte", "Transporte"
        GRAFICA = "grafica", "Gráfica"
        EVENTOS = "eventos", "Eventos"
        MARKETING = "marketing", "Marketing"
        TECNOLOGIA = "tecnologia", "Tecnologia"
        PATROCINIO = "patrocinio", "Patrocínio"
        SERVICOS = "servicos", "Serviços gerais"
        OUTROS = "outros", "Outros"

    class Status(models.TextChoices):
        ATIVO = "ativo", "Ativo"
        INATIVO = "inativo", "Inativo"

    nome = models.CharField("razão social ou nome", max_length=160)
    nome_fantasia = models.CharField("nome fantasia", max_length=160, blank=True)
    documento = models.CharField("CNPJ / CPF", max_length=20, blank=True)

    contato_nome = models.CharField("pessoa de contato", max_length=120, blank=True)
    email = models.EmailField("e-mail", blank=True)
    telefone = models.CharField("telefone", max_length=40, blank=True)
    whatsapp = models.CharField("WhatsApp", max_length=40, blank=True)
    endereco = models.CharField("endereço", max_length=255, blank=True)

    categoria = models.CharField(
        "categoria", max_length=20, choices=Categoria.choices,
        default=Categoria.OUTROS
    )
    produtos_servicos = models.TextField("produtos ou serviços fornecidos", blank=True)
    condicoes_comerciais = models.TextField("condições comerciais", blank=True)
    prazo_medio_entrega = models.CharField(
        "prazo médio de entrega", max_length=60, blank=True
    )
    status = models.CharField(
        "status", max_length=10, choices=Status.choices, default=Status.ATIVO
    )
    contrato = models.FileField(
        "contrato / documento", upload_to="fornecedores/", blank=True, null=True
    )
    observacoes = models.TextField("observações", blank=True)

    criado_em = models.DateTimeField("cadastrado em", auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="fornecedores_criados", verbose_name="cadastrado por"
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "fornecedor"
        verbose_name_plural = "fornecedores"
        ordering = ["nome"]

    def __str__(self):
        return self.nome_fantasia or self.nome

    def get_absolute_url(self):
        return reverse("fornecedores:detalhe", args=[self.pk])

    @property
    def nota_media(self):
        from django.db.models import Avg
        agg = self.avaliacoes.aggregate(
            m=Avg(
                (models.F("preco") + models.F("qualidade") + models.F("prazo")
                 + models.F("atendimento") + models.F("confiabilidade")) / 5.0
            )
        )
        return agg["m"]


class AvaliacaoFornecedor(models.Model):
    NOTAS = [(i, str(i)) for i in range(1, 6)]

    fornecedor = models.ForeignKey(
        Fornecedor, on_delete=models.CASCADE, related_name="avaliacoes",
        verbose_name="fornecedor"
    )
    preco = models.PositiveSmallIntegerField("preço", choices=NOTAS, default=3)
    qualidade = models.PositiveSmallIntegerField("qualidade", choices=NOTAS, default=3)
    prazo = models.PositiveSmallIntegerField("prazo", choices=NOTAS, default=3)
    atendimento = models.PositiveSmallIntegerField(
        "atendimento", choices=NOTAS, default=3
    )
    confiabilidade = models.PositiveSmallIntegerField(
        "confiabilidade", choices=NOTAS, default=3
    )
    comentario = models.TextField("comentário", blank=True)
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="avaliacoes_fornecedor", verbose_name="autor"
    )
    criado_em = models.DateTimeField("data", auto_now_add=True)

    class Meta:
        verbose_name = "avaliação de fornecedor"
        verbose_name_plural = "avaliações de fornecedor"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Avaliação de {self.fornecedor} ({self.media:.1f})"

    @property
    def media(self):
        return (
            self.preco + self.qualidade + self.prazo
            + self.atendimento + self.confiabilidade
        ) / 5
