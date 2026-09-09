"""Eventos da Atlética, com foco em FESTAS.

A modelagem espelha as planilhas Jungle / FRAT HOUSE:

* LoteIngresso  -> receita por lote (promocional, 1º lote, porta, promo grupo...)
* CustoEvento   -> custos fixos (local, som, segurança, DJ) e variáveis (bebidas)
* ReceitaEvento -> receitas extras fora ingresso (bar, patrocínio pontual)

O resultado (lucro/prejuízo), custo por pessoa e ponto de equilíbrio são
calculados a partir desses lançamentos.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from simple_history.models import HistoricalRecords

ZERO = Decimal("0")


class Evento(models.Model):
    class Tipo(models.TextChoices):
        FESTA = "festa", "Festa"
        JOGO = "jogo", "Jogo"
        TORNEIO = "torneio", "Torneio / Campeonato"
        CHURRASCO = "churrasco", "Churrasco / Resenha"
        VIAGEM = "viagem", "Viagem"
        JOGOS_UNIV = "jogos_univ", "Jogos universitários"
        VENDA_ESPECIAL = "venda", "Venda especial"
        ACADEMICO = "academico", "Evento acadêmico"
        OUTRO = "outro", "Outro"

    class Status(models.TextChoices):
        PLANEJAMENTO = "planejamento", "Em planejamento"
        CONFIRMADO = "confirmado", "Confirmado"
        REALIZADO = "realizado", "Realizado"
        CANCELADO = "cancelado", "Cancelado"

    nome = models.CharField("nome", max_length=160)
    tipo = models.CharField(
        "tipo", max_length=15, choices=Tipo.choices, default=Tipo.FESTA,
        db_index=True
    )
    descricao = models.TextField("descrição", blank=True)

    data = models.DateField("data", default=timezone.localdate)
    horario = models.CharField("horário", max_length=40, blank=True)
    local = models.CharField("local", max_length=200, blank=True)
    capacidade = models.PositiveIntegerField("capacidade", null=True, blank=True)
    publico_realizado = models.PositiveIntegerField(
        "público (realizado)", null=True, blank=True,
        help_text="Preencher depois do evento, se souber o número real.",
    )
    staff_cortesias = models.PositiveIntegerField(
        "staff / cortesias", default=0,
        help_text="Pessoas que entram sem pagar (não contam como receita).",
    )

    status = models.CharField(
        "status", max_length=15, choices=Status.choices,
        default=Status.PLANEJAMENTO, db_index=True
    )
    publico_alvo = models.CharField("público-alvo", max_length=160, blank=True)
    link_inscricao = models.URLField("link de inscrição / ingressos", blank=True)
    orcamento_previsto = models.DecimalField(
        "orçamento previsto (R$)", max_digits=12, decimal_places=2, default=0
    )

    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="eventos_responsavel", verbose_name="responsável"
    )
    fornecedores = models.ManyToManyField(
        "fornecedores.Fornecedor", blank=True, related_name="eventos",
        verbose_name="fornecedores envolvidos"
    )
    observacoes = models.TextField("observações", blank=True)

    demo = models.BooleanField(default=False, editable=False)
    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="eventos_criados", verbose_name="criado por"
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "evento"
        verbose_name_plural = "eventos"
        ordering = ["-data"]

    def __str__(self):
        return self.nome

    def get_absolute_url(self):
        return reverse("eventos:detalhe", args=[self.pk])

    @property
    def eh_festa(self):
        return self.tipo == self.Tipo.FESTA

    # -- Receitas ----------------------------------------------------------
    @property
    def ingressos_previstos(self):
        return sum((l.quantidade_prevista for l in self.lotes.all()), 0)

    @property
    def ingressos_vendidos(self):
        return sum((l.quantidade_vendida for l in self.lotes.all()), 0)

    @property
    def receita_ingressos(self):
        return sum((l.total_vendido for l in self.lotes.all()), ZERO)

    @property
    def receita_ingressos_prevista(self):
        return sum((l.total_previsto for l in self.lotes.all()), ZERO)

    @property
    def receita_extra(self):
        return sum((r.valor for r in self.receitas.all()), ZERO)

    @property
    def receita_total(self):
        return self.receita_ingressos + self.receita_extra

    # -- Custos ----------------------------------------------------------
    @property
    def custo_total(self):
        return sum((c.valor_total for c in self.custos.all()), ZERO)

    @property
    def custo_pago(self):
        return sum(
            (c.valor_pago for c in self.custos.all() if c.valor_pago), ZERO
        )

    @property
    def custo_a_pagar(self):
        return self.custo_total - self.custo_pago

    # -- Resultado -----------------------------------------------------
    @property
    def resultado(self):
        return self.receita_total - self.custo_total

    @property
    def margem(self):
        if not self.receita_total:
            return None
        return self.resultado / self.receita_total

    @property
    def publico_estimado(self):
        """Melhor número de pessoas disponível: realizado > vendidos+staff."""
        if self.publico_realizado:
            return self.publico_realizado
        return self.ingressos_vendidos + self.staff_cortesias

    @property
    def custo_por_pessoa(self):
        pessoas = self.publico_estimado
        if not pessoas:
            return None
        return self.custo_total / pessoas

    @property
    def ticket_medio(self):
        if not self.ingressos_vendidos:
            return None
        return self.receita_ingressos / self.ingressos_vendidos

    @property
    def breakeven_ingressos(self):
        """Quantos ingressos ao ticket médio cobrem o custo total."""
        tm = self.ticket_medio
        if not tm:
            return None
        import math

        return math.ceil((self.custo_total - self.receita_extra) / tm)


class LoteIngresso(models.Model):
    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name="lotes", verbose_name="evento"
    )
    nome = models.CharField("lote", max_length=80)
    quantidade_prevista = models.PositiveIntegerField("qtd. prevista", default=0)
    quantidade_vendida = models.PositiveIntegerField("qtd. vendida", default=0)
    valor_unitario = models.DecimalField(
        "valor unitário (R$)", max_digits=10, decimal_places=2, default=0
    )
    ordem = models.PositiveSmallIntegerField("ordem", default=0)

    class Meta:
        verbose_name = "lote de ingresso"
        verbose_name_plural = "lotes de ingresso"
        ordering = ["ordem", "id"]

    def __str__(self):
        return f"{self.nome} ({self.evento})"

    @property
    def total_previsto(self):
        return self.valor_unitario * self.quantidade_prevista

    @property
    def total_vendido(self):
        return self.valor_unitario * self.quantidade_vendida


class CustoEvento(models.Model):
    class Tipo(models.TextChoices):
        FIXO = "fixo", "Custo fixo"
        VARIAVEL = "variavel", "Custo variável"

    class Situacao(models.TextChoices):
        PENDENTE = "pendente", "A pagar"
        PARCIAL = "parcial", "Sinal pago"
        PAGO = "pago", "Pago"

    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name="custos", verbose_name="evento"
    )
    tipo = models.CharField(
        "tipo", max_length=10, choices=Tipo.choices, default=Tipo.FIXO
    )
    item = models.CharField("item", max_length=160)
    quantidade = models.DecimalField(
        "quantidade", max_digits=10, decimal_places=2, default=1
    )
    valor_unitario = models.DecimalField(
        "valor unitário (R$)", max_digits=10, decimal_places=2, default=0
    )
    valor_pago = models.DecimalField(
        "valor já pago (R$)", max_digits=10, decimal_places=2, default=0
    )
    situacao = models.CharField(
        "situação", max_length=10, choices=Situacao.choices,
        default=Situacao.PENDENTE
    )
    fornecedor = models.ForeignKey(
        "fornecedores.Fornecedor", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="custos_evento", verbose_name="fornecedor"
    )
    observacao = models.CharField("observação", max_length=255, blank=True)

    class Meta:
        verbose_name = "custo do evento"
        verbose_name_plural = "custos do evento"
        ordering = ["tipo", "item"]

    def __str__(self):
        return f"{self.item} — {self.evento}"

    @property
    def valor_total(self):
        return (self.quantidade or ZERO) * (self.valor_unitario or ZERO)


class ReceitaEvento(models.Model):
    class Origem(models.TextChoices):
        BAR = "bar", "Bar / bebidas"
        PATROCINIO = "patrocinio", "Patrocínio do evento"
        PARCERIA = "parceria", "Parceria"
        OUTRO = "outro", "Outro"

    evento = models.ForeignKey(
        Evento, on_delete=models.CASCADE, related_name="receitas",
        verbose_name="evento"
    )
    origem = models.CharField(
        "origem", max_length=15, choices=Origem.choices, default=Origem.OUTRO
    )
    descricao = models.CharField("descrição", max_length=200)
    valor = models.DecimalField("valor (R$)", max_digits=10, decimal_places=2)
    recebido = models.BooleanField("recebido", default=False)

    class Meta:
        verbose_name = "receita do evento"
        verbose_name_plural = "receitas do evento"
        ordering = ["-valor"]

    def __str__(self):
        return f"{self.descricao} — {self.evento}"
