"""Pedidos e vendas.

Regras de estoque (seção 8 do escopo):
* ao confirmar o pagamento o pedido dá baixa automática no estoque;
* ao cancelar ou devolver um pedido já baixado, a baixa é revertida (estorno);
* o controle usa o campo ``estoque_baixado`` para nunca baixar duas vezes.
"""

from decimal import Decimal

from django.conf import settings
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from simple_history.models import HistoricalRecords


class Pedido(models.Model):
    class Status(models.TextChoices):
        RASCUNHO = "rascunho", "Rascunho"
        AGUARDANDO = "aguardando_pagamento", "Aguardando pagamento"
        PAGO = "pago", "Pago"
        SEPARACAO = "em_separacao", "Em separação"
        PRONTO = "pronto", "Pronto para retirada"
        ENTREGUE = "entregue", "Entregue"
        CANCELADO = "cancelado", "Cancelado"
        DEVOLVIDO = "devolvido", "Devolvido"

    STATUS_BAIXA = {Status.PAGO, Status.SEPARACAO, Status.PRONTO, Status.ENTREGUE}
    STATUS_ESTORNO = {Status.CANCELADO, Status.DEVOLVIDO}

    class FormaPagamento(models.TextChoices):
        PIX = "pix", "PIX"
        DINHEIRO = "dinheiro", "Dinheiro"
        DEBITO = "debito", "Cartão de débito"
        CREDITO = "credito", "Cartão de crédito"
        TRANSFERENCIA = "transferencia", "Transferência"
        CORTESIA = "cortesia", "Cortesia"
        OUTRO = "outro", "Outro"

    class StatusPagamento(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        PARCIAL = "parcial", "Parcial"
        QUITADO = "quitado", "Quitado"

    numero = models.CharField(
        "número do pedido", max_length=20, unique=True, null=True, blank=True,
        default=None,
    )
    cliente = models.ForeignKey(
        "crm.Cliente", on_delete=models.PROTECT, related_name="pedidos",
        verbose_name="cliente"
    )
    status = models.CharField(
        "status do pedido", max_length=25, choices=Status.choices,
        default=Status.RASCUNHO, db_index=True
    )

    desconto = models.DecimalField(
        "desconto (R$)", max_digits=10, decimal_places=2, default=0
    )
    taxa = models.DecimalField(
        "taxa (R$)", max_digits=10, decimal_places=2, default=0
    )
    valor_total = models.DecimalField(
        "valor total (R$)", max_digits=10, decimal_places=2, default=0
    )

    forma_pagamento = models.CharField(
        "forma de pagamento", max_length=20, choices=FormaPagamento.choices,
        blank=True
    )
    status_pagamento = models.CharField(
        "status do pagamento", max_length=10, choices=StatusPagamento.choices,
        default=StatusPagamento.PENDENTE
    )

    data_compra = models.DateField("data da compra", default=timezone.localdate)
    data_entrega = models.DateField(
        "data de retirada / entrega", null=True, blank=True
    )
    local_retirada = models.CharField("local de retirada", max_length=160, blank=True)
    observacoes = models.TextField("observações", blank=True)
    comprovante = models.FileField(
        "comprovante", upload_to="pedidos/", blank=True, null=True
    )

    estoque_baixado = models.BooleanField("estoque baixado", default=False)

    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="pedidos_responsavel", verbose_name="responsável"
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="pedidos_criados", verbose_name="criado por"
    )
    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.numero or 'Rascunho'} - {self.cliente}"

    def get_absolute_url(self):
        return reverse("vendas:pedido_detalhe", args=[self.pk])

    # -- Calculos -------------------------------------------------------------
    @property
    def subtotal(self):
        return sum((i.total for i in self.itens.all()), Decimal("0"))

    def recalcular_total(self, salvar=True):
        self.valor_total = self.subtotal - (self.desconto or 0) + (self.taxa or 0)
        if self.valor_total < 0:
            self.valor_total = Decimal("0")
        if salvar:
            super().save(update_fields=["valor_total"])
        return self.valor_total

    @property
    def total_pago(self):
        return self.pagamentos.aggregate(t=models.Sum("valor"))["t"] or Decimal("0")

    @property
    def saldo_devedor(self):
        return (self.valor_total or Decimal("0")) - self.total_pago

    # -- Numeracao ---------------------------------------------------------
    def _gerar_numero(self):
        ano = timezone.now().year
        ultimo = (
            Pedido.objects.filter(numero__startswith=f"{ano}-")
            .order_by("-numero").first()
        )
        seq = 1
        if ultimo and "-" in ultimo.numero:
            try:
                seq = int(ultimo.numero.split("-")[1]) + 1
            except ValueError:
                pass
        return f"{ano}-{seq:04d}"

    def save(self, *args, **kwargs):
        if not self.numero and self.status != self.Status.RASCUNHO:
            self.numero = self._gerar_numero()
        super().save(*args, **kwargs)

    # -- Estoque ---------------------------------------------------------
    @transaction.atomic
    def aplicar_efeito_estoque(self, usuario=None):
        """Garante que o estoque reflita o status atual do pedido."""
        from apps.catalogo.models import MovimentacaoEstoque

        precisa_baixar = self.status in self.STATUS_BAIXA
        precisa_estornar = self.status in self.STATUS_ESTORNO

        if precisa_baixar and not self.estoque_baixado:
            for item in self.itens.select_related("produto"):
                item.produto.aplicar_movimentacao(
                    tipo=MovimentacaoEstoque.Tipo.SAIDA_VENDA,
                    quantidade=item.quantidade, usuario=usuario,
                    motivo=f"Pedido {self.numero}", pedido=self,
                )
            Pedido.objects.filter(pk=self.pk).update(estoque_baixado=True)
            self.estoque_baixado = True

        elif precisa_estornar and self.estoque_baixado:
            for item in self.itens.select_related("produto"):
                item.produto.aplicar_movimentacao(
                    tipo=MovimentacaoEstoque.Tipo.DEVOLUCAO,
                    quantidade=item.quantidade, usuario=usuario,
                    motivo=f"Estorno do pedido {self.numero}", pedido=self,
                )
            Pedido.objects.filter(pk=self.pk).update(estoque_baixado=False)
            self.estoque_baixado = False

    def itens_sem_estoque(self):
        faltas = []
        for item in self.itens.select_related("produto"):
            if item.quantidade > item.produto.quantidade_atual:
                faltas.append(
                    (item.produto, item.quantidade, item.produto.quantidade_atual)
                )
        return faltas


class ItemPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE, related_name="itens", verbose_name="pedido"
    )
    produto = models.ForeignKey(
        "catalogo.Produto", on_delete=models.PROTECT, related_name="itens_pedido",
        verbose_name="produto"
    )
    quantidade = models.PositiveIntegerField("quantidade", default=1)
    preco_unitario = models.DecimalField(
        "preço unitário (R$)", max_digits=10, decimal_places=2
    )
    desconto_item = models.DecimalField(
        "desconto do item (R$)", max_digits=10, decimal_places=2, default=0
    )

    class Meta:
        verbose_name = "item do pedido"
        verbose_name_plural = "itens do pedido"

    def __str__(self):
        return f"{self.quantidade}x {self.produto}"

    @property
    def total(self):
        return (self.preco_unitario * self.quantidade) - (self.desconto_item or 0)


class Pagamento(models.Model):
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE, related_name="pagamentos",
        verbose_name="pedido"
    )
    valor = models.DecimalField("valor (R$)", max_digits=10, decimal_places=2)
    forma = models.CharField(
        "forma", max_length=20, choices=Pedido.FormaPagamento.choices
    )
    data = models.DateField("data", default=timezone.localdate)
    observacao = models.CharField("observação", max_length=255, blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="pagamentos_registrados", verbose_name="registrado por"
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "pagamento"
        verbose_name_plural = "pagamentos"
        ordering = ["-data"]

    def __str__(self):
        return f"R$ {self.valor} - {self.pedido}"
