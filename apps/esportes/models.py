"""Esportes da Atlética: o que foi orçado para cada modalidade e o que foi gasto.

A modelagem espelha as duas planilhas da diretoria de Esportes:

* Orçamento (aba "Gastos 2026") -> Modalidade + OrcamentoModalidade, uma linha
  por modalidade com custo de quadra, de treinador e quantos treinos e jogos
  estão previstos em cada semestre.
* Treinos (uma aba por esporte) -> Sessao, um treino ou jogo por linha, com
  "Sim/Não" para confirmado, técnico e quadra.

As duas entram pela sincronização (Fontes de planilha). A planilha continua
sendo a fonte da verdade: o CRM não edita esses dados, só mostra.
"""

from decimal import Decimal

from django.db import models

ZERO = Decimal("0")

#: Até julho é o primeiro semestre: na FGV o 1º termina no começo de julho e a
#: planilha "Treinos 26.1" tem treinos até meados de julho.
ULTIMO_MES_DO_1O_SEMESTRE = 7


def semestre_de(data) -> int:
    return 1 if data.month <= ULTIMO_MES_DO_1O_SEMESTRE else 2


def meses_do_semestre(semestre: int) -> range:
    if semestre == 1:
        return range(1, ULTIMO_MES_DO_1O_SEMESTRE + 1)
    return range(ULTIMO_MES_DO_1O_SEMESTRE + 1, 13)


class Modalidade(models.Model):
    class Naipe(models.TextChoices):
        MASCULINO = "masc", "Masculino"
        FEMININO = "fem", "Feminino"
        MISTO = "misto", "Misto"

    esporte = models.CharField("esporte", max_length=60)
    naipe = models.CharField(
        "naipe", max_length=5, choices=Naipe.choices, default=Naipe.MISTO
    )
    dia_semana = models.CharField("dia do treino", max_length=20, blank=True)
    horario_inicio = models.TimeField("início", null=True, blank=True)
    horario_fim = models.TimeField("término", null=True, blank=True)
    local = models.CharField("local", max_length=160, blank=True)
    atualizado_em = models.DateTimeField("atualizada em", auto_now=True)

    class Meta:
        verbose_name = "modalidade"
        verbose_name_plural = "modalidades"
        ordering = ["esporte", "naipe"]
        constraints = [
            models.UniqueConstraint(fields=["esporte", "naipe"], name="modalidade_unica")
        ]

    def __str__(self):
        return self.nome

    @property
    def nome(self):
        if self.naipe == self.Naipe.MISTO:
            return self.esporte
        return f"{self.esporte} {self.get_naipe_display()}"


class OrcamentoModalidade(models.Model):
    modalidade = models.ForeignKey(
        Modalidade, on_delete=models.CASCADE, related_name="orcamentos",
        verbose_name="modalidade",
    )
    ano = models.PositiveSmallIntegerField("ano")
    semestre = models.PositiveSmallIntegerField("semestre", choices=[(1, "1º"), (2, "2º")])
    custo_quadra_hora = models.DecimalField(
        "quadra por hora (R$)", max_digits=10, decimal_places=2, default=0
    )
    custo_treinador_treino = models.DecimalField(
        "treinador por treino (R$)", max_digits=10, decimal_places=2, default=0
    )
    custo_treinador_jogo = models.DecimalField(
        "treinador por jogo (R$)", max_digits=10, decimal_places=2, default=0
    )
    treinos_previstos = models.PositiveIntegerField("treinos previstos", default=0)
    jogos_previstos = models.PositiveIntegerField("jogos previstos", default=0)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "orçamento de modalidade"
        verbose_name_plural = "orçamentos de modalidade"
        ordering = ["-ano", "semestre", "modalidade"]
        constraints = [
            models.UniqueConstraint(
                fields=["modalidade", "ano", "semestre"], name="orcamento_unico_semestre"
            )
        ]

    def __str__(self):
        return f"{self.modalidade} {self.ano}.{self.semestre}"

    @property
    def total_previsto(self) -> Decimal:
        """Mesma conta da planilha: cada treino paga quadra e treinador, cada
        jogo paga só o treinador."""
        return (
            self.treinos_previstos * (self.custo_quadra_hora + self.custo_treinador_treino)
            + self.jogos_previstos * self.custo_treinador_jogo
        )


class Sessao(models.Model):
    class Tipo(models.TextChoices):
        TREINO = "treino", "Treino"
        JOGO = "jogo", "Jogo"

    modalidade = models.ForeignKey(
        Modalidade, on_delete=models.CASCADE, related_name="sessoes",
        verbose_name="modalidade",
    )
    tipo = models.CharField("tipo", max_length=6, choices=Tipo.choices, default=Tipo.TREINO)
    data = models.DateField("data", db_index=True)
    confirmada = models.BooleanField("confirmado", default=True)
    teve_tecnico = models.BooleanField("teve técnico", default=False)
    teve_quadra = models.BooleanField("teve quadra", default=False)
    custo_tecnico = models.DecimalField(
        "valor do técnico (R$)", max_digits=10, decimal_places=2, default=0,
        help_text="Valor unitário que a planilha usava na data da importação.",
    )
    custo_quadra = models.DecimalField(
        "valor da quadra (R$)", max_digits=10, decimal_places=2, default=0
    )
    custo = models.DecimalField(
        "custo (R$)", max_digits=10, decimal_places=2, default=0,
        help_text="Técnico e quadra que de fato foram usados.",
    )
    observacao = models.CharField("observação", max_length=120, blank=True)
    origem = models.CharField(
        "origem", max_length=160, blank=True,
        help_text="Aba e célula da planilha de onde a linha veio.",
    )

    class Meta:
        verbose_name = "treino ou jogo"
        verbose_name_plural = "treinos e jogos"
        ordering = ["-data", "modalidade"]
        constraints = [
            models.UniqueConstraint(
                fields=["modalidade", "tipo", "data"], name="sessao_unica_no_dia"
            )
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} {self.modalidade} {self.data:%d/%m/%Y}"

    def calcular_custo(self) -> Decimal:
        return (self.custo_tecnico if self.teve_tecnico else ZERO) + (
            self.custo_quadra if self.teve_quadra else ZERO
        )
