"""Catálogo e estoque: produtos, categorias e movimentações de estoque.

O saldo de cada produto (``quantidade_atual``) é mantido pela aplicação a cada
MovimentacaoEstoque criada — nunca editado à mão. Assim toda alteração de saldo
fica rastreável (seções 7 e 14 do escopo).
"""

from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from simple_history.models import HistoricalRecords


class CategoriaProduto(models.Model):
    nome = models.CharField("nome", max_length=60, unique=True)
    descricao = models.CharField("descrição", max_length=255, blank=True)
    ativo = models.BooleanField("ativa", default=True)

    class Meta:
        verbose_name = "categoria de produto"
        verbose_name_plural = "categorias de produto"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Produto(models.Model):
    class Status(models.TextChoices):
        ATIVO = "ativo", "Ativo"
        INATIVO = "inativo", "Inativo"

    nome = models.CharField("nome", max_length=160)
    codigo_interno = models.CharField(
        "código interno", max_length=40, blank=True, db_index=True
    )
    sku = models.CharField("SKU", max_length=60, blank=True, db_index=True)
    categoria = models.ForeignKey(
        CategoriaProduto, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="produtos", verbose_name="categoria"
    )
    descricao = models.TextField("descrição", blank=True)
    foto = models.ImageField("foto", upload_to="produtos/", blank=True, null=True)

    tamanho = models.CharField("tamanho", max_length=20, blank=True)
    cor = models.CharField("cor", max_length=40, blank=True)
    marca = models.CharField("marca", max_length=60, blank=True)
    fornecedor = models.ForeignKey(
        "fornecedores.Fornecedor", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="produtos", verbose_name="fornecedor"
    )

    custo_unitario = models.DecimalField(
        "custo unitário (R$)", max_digits=10, decimal_places=2, default=0
    )
    preco_venda = models.DecimalField(
        "preço de venda (R$)", max_digits=10, decimal_places=2, default=0
    )

    quantidade_atual = models.IntegerField("quantidade em estoque", default=0)
    estoque_minimo = models.IntegerField("estoque mínimo", default=0)
    estoque_maximo = models.IntegerField("estoque máximo", null=True, blank=True)
    localizacao = models.CharField("localização física", max_length=120, blank=True)

    status = models.CharField(
        "status", max_length=10, choices=Status.choices, default=Status.ATIVO
    )
    observacoes = models.TextField("observações", blank=True)
    criado_em = models.DateTimeField("cadastrado em", auto_now_add=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="produtos_criados", verbose_name="cadastrado por"
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "produto"
        verbose_name_plural = "produtos"
        ordering = ["nome"]

    def __str__(self):
        partes = [self.nome]
        if self.tamanho:
            partes.append(self.tamanho)
        if self.cor:
            partes.append(self.cor)
        return " · ".join(partes)

    def get_absolute_url(self):
        return reverse("catalogo:produto_detalhe", args=[self.pk])

    @property
    def margem_estimada(self):
        if not self.preco_venda:
            return None
        return (self.preco_venda - self.custo_unitario) / self.preco_venda

    @property
    def valor_em_estoque(self):
        return (self.custo_unitario or Decimal("0")) * self.quantidade_atual

    @property
    def esgotado(self):
        return self.quantidade_atual <= 0

    @property
    def estoque_baixo(self):
        return 0 < self.quantidade_atual <= self.estoque_minimo

    def aplicar_movimentacao(self, *, tipo, quantidade, usuario=None, motivo="",
                             pedido=None, evento=None, observacao=""):
        """Cria a MovimentacaoEstoque e atualiza o saldo do produto."""
        mov = MovimentacaoEstoque(
            produto=self, tipo=tipo, quantidade=quantidade, usuario=usuario,
            motivo=motivo, pedido=pedido, observacao=observacao,
        )
        mov.save()  # o save() da movimentação ajusta o saldo
        return mov


class MovimentacaoEstoque(models.Model):
    class Tipo(models.TextChoices):
        ENTRADA = "entrada", "Entrada de mercadoria"
        SAIDA_VENDA = "saida_venda", "Saída por venda"
        SAIDA_EVENTO = "saida_evento", "Saída para evento"
        SAIDA_DOACAO = "saida_doacao", "Saída por doação"
        PERDA = "perda", "Perda / avaria"
        AJUSTE_POSITIVO = "ajuste_pos", "Ajuste (entrada)"
        AJUSTE_NEGATIVO = "ajuste_neg", "Ajuste (saída)"
        DEVOLUCAO = "devolucao", "Devolução (entrada)"
        TRANSFERENCIA = "transferencia", "Transferência entre locais"

    ENTRADAS = {
        Tipo.ENTRADA, Tipo.AJUSTE_POSITIVO, Tipo.DEVOLUCAO,
    }

    produto = models.ForeignKey(
        Produto, on_delete=models.CASCADE, related_name="movimentacoes",
        verbose_name="produto"
    )
    tipo = models.CharField("tipo de movimentação", max_length=20, choices=Tipo.choices)
    quantidade = models.PositiveIntegerField("quantidade")
    saldo_apos = models.IntegerField("saldo após", null=True, blank=True)
    data = models.DateTimeField("data", auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="movimentacoes_estoque", verbose_name="responsável"
    )
    motivo = models.CharField("motivo", max_length=160, blank=True)
    pedido = models.ForeignKey(
        "vendas.Pedido", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="movimentacoes", verbose_name="pedido relacionado"
    )
    observacao = models.CharField("observação", max_length=255, blank=True)

    class Meta:
        verbose_name = "movimentação de estoque"
        verbose_name_plural = "movimentações de estoque"
        ordering = ["-data"]

    def __str__(self):
        return f"{self.get_tipo_display()} · {self.quantidade} · {self.produto}"

    @property
    def eh_entrada(self):
        return self.tipo in self.ENTRADAS

    def save(self, *args, **kwargs):
        nova = self._state.adding
        if nova:
            delta = self.quantidade if self.eh_entrada else -self.quantidade
            Produto.objects.filter(pk=self.produto_id).update(
                quantidade_atual=models.F("quantidade_atual") + delta
            )
            self.produto.refresh_from_db(fields=["quantidade_atual"])
            self.saldo_apos = self.produto.quantidade_atual
        super().save(*args, **kwargs)
