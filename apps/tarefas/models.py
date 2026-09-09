"""Tarefas e atividades da equipe."""

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Tarefa(models.Model):
    class Prioridade(models.TextChoices):
        BAIXA = "baixa", "Baixa"
        NORMAL = "normal", "Normal"
        ALTA = "alta", "Alta"
        URGENTE = "urgente", "Urgente"

    class Status(models.TextChoices):
        A_FAZER = "a_fazer", "A fazer"
        EM_ANDAMENTO = "em_andamento", "Em andamento"
        AGUARDANDO = "aguardando", "Aguardando"
        CONCLUIDA = "concluida", "Concluída"
        CANCELADA = "cancelada", "Cancelada"

    titulo = models.CharField("título", max_length=160)
    descricao = models.TextField("descrição", blank=True)

    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="tarefas_atribuidas", verbose_name="responsável"
    )
    criador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="tarefas_criadas", verbose_name="criador"
    )

    prazo = models.DateField("prazo", null=True, blank=True)
    prioridade = models.CharField(
        "prioridade", max_length=10, choices=Prioridade.choices,
        default=Prioridade.NORMAL
    )
    status = models.CharField(
        "status", max_length=15, choices=Status.choices, default=Status.A_FAZER,
        db_index=True
    )

    cliente = models.ForeignKey(
        "crm.Cliente", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="tarefas", verbose_name="cliente relacionado"
    )
    pedido = models.ForeignKey(
        "vendas.Pedido", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="tarefas", verbose_name="pedido relacionado"
    )
    fornecedor = models.ForeignKey(
        "fornecedores.Fornecedor", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="tarefas", verbose_name="fornecedor relacionado"
    )

    anexo = models.FileField("anexo", upload_to="tarefas/", blank=True, null=True)

    criado_em = models.DateTimeField("criada em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizada em", auto_now=True)
    concluida_em = models.DateTimeField("concluída em", null=True, blank=True)

    class Meta:
        verbose_name = "tarefa"
        verbose_name_plural = "tarefas"
        ordering = ["status", "prazo", "-prioridade"]

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse("tarefas:detalhe", args=[self.pk])

    @property
    def atrasada(self):
        return (
            self.prazo is not None
            and self.status not in {self.Status.CONCLUIDA, self.Status.CANCELADA}
            and self.prazo < timezone.localdate()
        )

    def save(self, *args, **kwargs):
        if self.status == self.Status.CONCLUIDA and self.concluida_em is None:
            self.concluida_em = timezone.now()
        if self.status != self.Status.CONCLUIDA:
            self.concluida_em = None
        super().save(*args, **kwargs)


class ComentarioTarefa(models.Model):
    tarefa = models.ForeignKey(
        Tarefa, on_delete=models.CASCADE, related_name="comentarios",
        verbose_name="tarefa"
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="comentarios_tarefa", verbose_name="autor"
    )
    texto = models.TextField("comentário")
    criado_em = models.DateTimeField("data", auto_now_add=True)

    class Meta:
        verbose_name = "comentário de tarefa"
        verbose_name_plural = "comentários de tarefa"
        ordering = ["criado_em"]

    def __str__(self):
        return f"Comentário de {self.autor} em {self.tarefa}"
