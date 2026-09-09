"""CRM: clientes/contatos, categorias, tags e histórico de interações."""

from django.conf import settings
from django.db import models
from django.urls import reverse
from simple_history.models import HistoricalRecords


class CategoriaCliente(models.Model):
    """Categoria editável pelo administrador (Aluno FGV, Torcedor, Atleta...)."""

    nome = models.CharField("nome", max_length=60, unique=True)
    cor = models.CharField("cor", max_length=7, default="#6c757d")
    ativo = models.BooleanField("ativa", default=True)

    class Meta:
        verbose_name = "categoria de cliente"
        verbose_name_plural = "categorias de cliente"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Tag(models.Model):
    nome = models.CharField("nome", max_length=40, unique=True)
    cor = models.CharField("cor", max_length=7, default="#0d6efd")

    class Meta:
        verbose_name = "tag"
        verbose_name_plural = "tags"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Cliente(models.Model):
    class Vinculo(models.TextChoices):
        ALUNO = "aluno", "Aluno FGV"
        EX_ALUNO = "ex_aluno", "Ex-aluno"
        FUNCIONARIO = "funcionario", "Funcionário FGV"
        EXTERNO = "externo", "Sem vínculo com a FGV"
        OUTRO = "outro", "Outro"

    class Relacionamento(models.TextChoices):
        NOVO = "novo", "Novo contato"
        ATIVO = "ativo", "Ativo"
        RECORRENTE = "recorrente", "Recorrente"
        INATIVO = "inativo", "Inativo"

    # Identificação
    nome = models.CharField("nome completo", max_length=160)
    nome_social = models.CharField("nome social", max_length=160, blank=True)
    cpf = models.CharField("CPF", max_length=14, blank=True)
    data_nascimento = models.DateField("data de nascimento", null=True, blank=True)

    # Contato
    email = models.EmailField("e-mail", blank=True)
    telefone = models.CharField("telefone", max_length=40, blank=True)
    whatsapp = models.CharField("WhatsApp", max_length=40, blank=True)
    cidade = models.CharField("cidade", max_length=120, blank=True)
    endereco = models.CharField("endereço", max_length=255, blank=True)

    # Vínculo acadêmico
    membro_fgv = models.BooleanField("é da comunidade FGV?", default=True)
    vinculo = models.CharField(
        "tipo de vínculo", max_length=20, choices=Vinculo.choices,
        default=Vinculo.ALUNO
    )
    curso = models.CharField("curso", max_length=120, blank=True)
    periodo = models.CharField("período", max_length=30, blank=True)
    campus = models.CharField("campus", max_length=120, blank=True)
    turma = models.CharField("turma", max_length=60, blank=True)

    # Classificação
    categoria = models.ForeignKey(
        CategoriaCliente, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="clientes", verbose_name="categoria"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="clientes")
    origem = models.CharField("origem do contato", max_length=120, blank=True)
    relacionamento = models.CharField(
        "status do relacionamento", max_length=20,
        choices=Relacionamento.choices, default=Relacionamento.NOVO
    )
    aceita_comunicacoes = models.BooleanField(
        "autoriza receber comunicações", default=False,
        help_text="Consentimento para e-mail/WhatsApp (LGPD).",
    )

    observacoes = models.TextField("observações", blank=True)

    criado_em = models.DateTimeField("cadastrado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="clientes_criados", verbose_name="cadastrado por"
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["nome"]
        indexes = [
            models.Index(fields=["nome"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return self.nome_social or self.nome

    def get_absolute_url(self):
        return reverse("crm:cliente_detalhe", args=[self.pk])

    @property
    def total_gasto(self):
        from django.db.models import Sum
        return (
            self.pedidos.filter(status=self._status_pago())
            .aggregate(t=Sum("valor_total"))["t"] or 0
        )

    @staticmethod
    def _status_pago():
        return "pago"


class Interacao(models.Model):
    class Tipo(models.TextChoices):
        LIGACAO = "ligacao", "Ligação"
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "E-mail"
        PRESENCIAL = "presencial", "Presencial"
        OUTRO = "outro", "Outro"

    cliente = models.ForeignKey(
        Cliente, on_delete=models.CASCADE, related_name="interacoes",
        verbose_name="cliente"
    )
    tipo = models.CharField("tipo", max_length=20, choices=Tipo.choices)
    resumo = models.CharField("resumo", max_length=255)
    detalhe = models.TextField("detalhe", blank=True)
    data = models.DateTimeField("data")
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="interacoes_registradas", verbose_name="registrado por"
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "interação"
        verbose_name_plural = "interações"
        ordering = ["-data"]

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.cliente}"
