"""Lógica de produtos/estoque compartilhada pela tela antiga e pela API."""

from django.db import transaction
from django.db.models import F, Q

from apps.nucleo.models import registrar_atividade
from apps.relatorios.services import csv_response

from .models import MovimentacaoEstoque, Produto


def buscar(qs, termo: str):
    termo = (termo or "").strip()
    if not termo:
        return qs
    return qs.filter(
        Q(nome__icontains=termo) | Q(codigo_interno__icontains=termo)
        | Q(sku__icontains=termo) | Q(marca__icontains=termo) | Q(cor__icontains=termo)
    )


def filtrar_situacao(qs, situacao: str | None):
    if situacao == "baixo":
        return qs.filter(quantidade_atual__gt=0, quantidade_atual__lte=F("estoque_minimo"))
    if situacao == "esgotado":
        return qs.filter(quantidade_atual__lte=0)
    if situacao == "ok":
        return qs.filter(quantidade_atual__gt=F("estoque_minimo"))
    return qs


def situacao(produto: Produto) -> str:
    if produto.quantidade_atual <= 0:
        return "esgotado"
    if produto.quantidade_atual <= produto.estoque_minimo:
        return "baixo"
    return "ok"


def url_spa(produto: Produto) -> str:
    return f"/produtos/{produto.pk}"


def registrar(usuario, verbo: str, produto: Produto, descricao: str = ""):
    registrar_atividade(usuario, verbo, str(produto), descricao, url=url_spa(produto))


@transaction.atomic
def movimentar(produto: Produto, *, tipo: str, quantidade: int, usuario, motivo: str = "",
               observacao: str = "") -> MovimentacaoEstoque:
    """Única porta de entrada para mexer no saldo (fora dos pedidos)."""
    produto = Produto.objects.select_for_update().get(pk=produto.pk)
    mov = produto.aplicar_movimentacao(
        tipo=tipo, quantidade=quantidade, usuario=usuario, motivo=motivo, observacao=observacao,
    )
    registrar(usuario, f"movimentou estoque ({mov.get_tipo_display()})", produto,
              f"{quantidade} un. → saldo {mov.saldo_apos}")
    return mov


def exportar_csv(qs=None):
    qs = qs if qs is not None else Produto.objects.all()
    qs = qs.select_related("categoria").order_by("nome")
    return csv_response(
        "inventario",
        ["nome", "tamanho", "cor", "sku", "codigo_interno", "categoria", "saldo", "estoque_minimo",
         "custo_unitario", "preco_venda", "valor_em_estoque", "status"],
        [[p.nome, p.tamanho, p.cor, p.sku, p.codigo_interno, p.categoria.nome if p.categoria else "",
          p.quantidade_atual, p.estoque_minimo, p.custo_unitario, p.preco_venda,
          p.valor_em_estoque, p.get_status_display()] for p in qs],
    )
