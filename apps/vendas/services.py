"""Regras de pedido em um lugar só (tela antiga e API).

Estoque:
- entrar em PAGO/SEPARAÇÃO/PRONTO/ENTREGUE baixa os itens uma única vez
  (``estoque_baixado``); CANCELADO/DEVOLVIDO estorna;
- editar os itens de um pedido já baixado estorna os itens antigos e baixa os
  novos, para o saldo nunca ficar duplicado nem desatualizado;
- confirmar sem saldo suficiente é recusado com ``EstoqueInsuficiente``.
"""

from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import Q

from apps.catalogo.models import MovimentacaoEstoque, Produto
from apps.contas.models import PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_FINANCEIRO
from apps.nucleo.models import registrar_atividade

from .models import ItemPedido, Pagamento, Pedido


class EstoqueInsuficiente(Exception):
    def __init__(self, faltas):
        self.faltas = faltas  # [(produto, necessario, disponivel)]
        nomes = ", ".join(f"{p} (tem {d}, precisa {n})" for p, n, d in faltas)
        super().__init__(f"Estoque insuficiente: {nomes}.")

    def como_lista(self):
        return [
            {"produto_id": p.id, "produto": str(p), "necessario": n, "disponivel": d}
            for p, n, d in self.faltas
        ]


def buscar(qs, termo: str):
    termo = (termo or "").strip()
    if not termo:
        return qs
    return qs.filter(
        Q(numero__icontains=termo) | Q(cliente__nome__icontains=termo)
        | Q(itens__produto__nome__icontains=termo)
    ).distinct()


def url_spa(pedido: Pedido) -> str:
    return f"/pedidos/{pedido.pk}"


def rotulo(pedido: Pedido) -> str:
    return pedido.numero or f"rascunho #{pedido.pk}"


def pode_registrar_pagamento(user) -> bool:
    return user.is_superuser or bool(
        {PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_FINANCEIRO} & set(user.perfis)
    )


def _faltas(pedido: Pedido, itens=None):
    itens = itens if itens is not None else list(pedido.itens.select_related("produto"))
    faltas = []
    for item in itens:
        produto = item.produto
        produto.refresh_from_db(fields=["quantidade_atual"])
        if item.quantidade > produto.quantidade_atual:
            faltas.append((produto, item.quantidade, produto.quantidade_atual))
    return faltas


def _estornar(pedido: Pedido, usuario, motivo: str):
    for item in pedido.itens.select_related("produto"):
        item.produto.aplicar_movimentacao(
            tipo=MovimentacaoEstoque.Tipo.DEVOLUCAO, quantidade=item.quantidade,
            usuario=usuario, motivo=motivo, pedido=pedido,
        )
    Pedido.objects.filter(pk=pedido.pk).update(estoque_baixado=False)
    pedido.estoque_baixado = False


@transaction.atomic
def salvar_pedido(pedido: Pedido, dados: dict, itens: list[dict] | None, usuario) -> Pedido:
    """``dados``: campos do pedido. ``itens``: lista completa desejada
    (``{"id"?, "produto", "quantidade", "preco_unitario", "desconto_item"}``);
    ``None`` = não mexer nos itens."""
    novo = pedido.pk is None
    if not novo:
        pedido = Pedido.objects.select_for_update().get(pk=pedido.pk)

    # Itens de pedido já baixado vão mudar: devolve o que estava baixado antes.
    if itens is not None and pedido.estoque_baixado:
        _estornar(pedido, usuario, f"Ajuste de itens do pedido {rotulo(pedido)}")

    for campo, valor in dados.items():
        setattr(pedido, campo, valor)
    if novo:
        pedido.criado_por = usuario
    pedido.save()

    if itens is not None:
        _sincronizar_itens(pedido, itens)

    pedido.recalcular_total()

    if pedido.status in Pedido.STATUS_BAIXA and not pedido.estoque_baixado:
        faltas = _faltas(pedido)
        if faltas:
            raise EstoqueInsuficiente(faltas)
    pedido.aplicar_efeito_estoque(usuario=usuario)

    registrar_atividade(usuario, "criou pedido" if novo else "editou pedido",
                        rotulo(pedido), url=url_spa(pedido))
    return pedido


def _sincronizar_itens(pedido: Pedido, itens: list[dict]):
    existentes = {i.id: i for i in pedido.itens.all()}
    manter = set()
    for dado in itens:
        produto = dado["produto"]
        if isinstance(produto, int):
            produto = Produto.objects.get(pk=produto)
        item_id = dado.get("id")
        item = existentes.get(item_id) if item_id else None
        if item is None:
            item = ItemPedido(pedido=pedido)
        item.produto = produto
        item.quantidade = dado["quantidade"]
        item.preco_unitario = dado.get("preco_unitario")
        if item.preco_unitario is None:
            item.preco_unitario = produto.preco_venda
        item.desconto_item = dado.get("desconto_item") or Decimal("0")
        item.save()
        manter.add(item.id)
    for item_id, item in existentes.items():
        if item_id not in manter:
            item.delete()


@transaction.atomic
def mudar_status(pedido: Pedido, novo: str, usuario) -> Pedido:
    if novo not in dict(Pedido.Status.choices):
        raise ValueError("Status inválido.")
    pedido = Pedido.objects.select_for_update().get(pk=pedido.pk)
    if novo in Pedido.STATUS_BAIXA and not pedido.estoque_baixado:
        faltas = _faltas(pedido)
        if faltas:
            raise EstoqueInsuficiente(faltas)
    pedido.status = novo
    pedido.save()
    pedido.aplicar_efeito_estoque(usuario=usuario)
    registrar_atividade(usuario, "mudou status do pedido",
                        f"{rotulo(pedido)} → {pedido.get_status_display()}", url=url_spa(pedido))
    return pedido


def atualizar_status_pagamento(pedido: Pedido):
    if pedido.valor_total and pedido.saldo_devedor <= 0:
        pedido.status_pagamento = Pedido.StatusPagamento.QUITADO
    elif pedido.total_pago > 0:
        pedido.status_pagamento = Pedido.StatusPagamento.PARCIAL
    else:
        pedido.status_pagamento = Pedido.StatusPagamento.PENDENTE
    pedido.save(update_fields=["status_pagamento"])


@transaction.atomic
def registrar_pagamento(pedido: Pedido, dados: dict, usuario) -> Pagamento:
    pagamento = Pagamento.objects.create(pedido=pedido, registrado_por=usuario, **dados)
    atualizar_status_pagamento(pedido)
    registrar_atividade(usuario, "registrou pagamento",
                        f"{rotulo(pedido)} — R$ {pagamento.valor}", url=url_spa(pedido))
    return pagamento


@transaction.atomic
def excluir_pagamento(pedido: Pedido, pagamento_id: int, usuario) -> bool:
    apagados, _ = pedido.pagamentos.filter(pk=pagamento_id).delete()
    if apagados:
        atualizar_status_pagamento(pedido)
        registrar_atividade(usuario, "removeu pagamento", rotulo(pedido), url=url_spa(pedido))
    return bool(apagados)


@transaction.atomic
def excluir_pedido(pedido: Pedido, usuario):
    if pedido.estoque_baixado:
        _estornar(pedido, usuario, f"Exclusão do pedido {rotulo(pedido)}")
    registrar_atividade(usuario, "excluiu pedido", rotulo(pedido))
    pedido.delete()
