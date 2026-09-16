"""Consultas dos relatórios, compartilhadas pela tela antiga e pela API.

Definições:
- **vendas**: pedidos no período, menos rascunho e cancelado (inclui os que
  ainda aguardam pagamento; é o "que foi vendido", não o "que entrou no caixa").
- **produtos vendidos**: itens desses mesmos pedidos.
- **estoque**: foto atual dos produtos (não depende de período).
- **clientes**: ranking por nº de pedidos; ``gasto`` só conta pedidos pagos,
  em separação, prontos ou entregues.
"""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal

from django.db.models import Count, DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse

from apps.catalogo.models import Produto
from apps.crm.models import Cliente
from apps.nucleo.services.dashboard import (
    STATUS_IGNORADOS, STATUS_RECEITA, distribuicao_status, formas_pagamento,
)
from apps.nucleo.services.periodos import Periodo, preencher_serie, primeiro_dia_do_mes
from apps.vendas.models import ItemPedido, Pedido

DEC = DecimalField(max_digits=12, decimal_places=2)
ZERO = Decimal("0")


def csv_response(nome: str, cabecalho: list[str], linhas) -> HttpResponse:
    resposta = HttpResponse(content_type="text/csv; charset=utf-8")
    resposta["Content-Disposition"] = f'attachment; filename="{nome}.csv"'
    resposta.write("﻿")  # BOM: o Excel abre com acentos certos
    escritor = csv.writer(resposta, delimiter=";")
    escritor.writerow(cabecalho)
    escritor.writerows(linhas)
    return resposta


# --------------------------------------------------------------------------- #
# Vendas por período
# --------------------------------------------------------------------------- #
def _pedidos_vendidos(inicio: date, fim: date):
    return Pedido.objects.filter(data_compra__range=(inicio, fim)).exclude(
        status__in=STATUS_IGNORADOS
    )


def _por_tempo(inicio: date, fim: date, granularidade: str) -> list[dict]:
    qs = _pedidos_vendidos(inicio, fim)
    if granularidade == "mes":
        from django.db.models.functions import TruncMonth

        qs = qs.annotate(_ponto=TruncMonth("data_compra"))
    else:
        qs = qs.annotate(_ponto=F("data_compra"))
    bruto = {}
    for l in qs.values("_ponto").annotate(
        total=Coalesce(Sum("valor_total"), Value(0), output_field=DEC), qtd=Count("id")
    ):
        ponto = l["_ponto"]
        if hasattr(ponto, "date"):
            ponto = ponto.date()
        if granularidade == "mes":
            ponto = primeiro_dia_do_mes(ponto)
        bruto[ponto] = {"total": l["total"], "qtd": l["qtd"]}
    return [
        {"data": d, "total": v["total"], "qtd": v["qtd"]}
        for d, v in preencher_serie(bruto, inicio, fim, granularidade, {"total": ZERO, "qtd": 0})
    ]


def vendas_periodo(periodo: Periodo) -> dict:
    qs = _pedidos_vendidos(periodo.inicio, periodo.fim)
    total = qs.aggregate(t=Coalesce(Sum("valor_total"), Value(0), output_field=DEC))["t"] or ZERO
    qtd = qs.count()
    serie = _por_tempo(periodo.inicio, periodo.fim, periodo.granularidade)
    if periodo.comparar:
        ant = periodo.anterior
        serie_ant = _por_tempo(ant.inicio, ant.fim, periodo.granularidade)
        for i, linha in enumerate(serie):
            linha["anterior"] = serie_ant[i]["total"] if i < len(serie_ant) else None
            linha["qtd_anterior"] = serie_ant[i]["qtd"] if i < len(serie_ant) else None
        qs_ant = _pedidos_vendidos(ant.inicio, ant.fim)
        total_ant = qs_ant.aggregate(t=Coalesce(Sum("valor_total"), Value(0), output_field=DEC))["t"] or ZERO
        qtd_ant = qs_ant.count()
    else:
        total_ant = qtd_ant = None
    return {
        "periodo": periodo.como_dict(),
        "total": total,
        "qtd": qtd,
        "ticket_medio": (total / qtd) if qtd else ZERO,
        "total_anterior": total_ant,
        "qtd_anterior": qtd_ant,
        "por_periodo": serie,
        "por_status": distribuicao_status(periodo.inicio, periodo.fim),
        "por_forma": formas_pagamento(periodo.inicio, periodo.fim),
    }


def vendas_csv(periodo: Periodo) -> HttpResponse:
    dados = vendas_periodo(periodo)
    return csv_response(
        f"vendas_{periodo.inicio}_{periodo.fim}",
        ["dia", "pedidos", "receita"],
        [[l["data"], l["qtd"], l["total"]] for l in dados["por_periodo"]],
    )


# --------------------------------------------------------------------------- #
# Produtos vendidos
# --------------------------------------------------------------------------- #
def produtos_vendidos(inicio: date, fim: date) -> dict:
    linhas = list(
        ItemPedido.objects.filter(pedido__data_compra__range=(inicio, fim))
        .exclude(pedido__status__in=STATUS_IGNORADOS)
        .values("produto_id", "produto__nome", "produto__tamanho",
                "produto__categoria__nome", "produto__sku")
        .annotate(
            qtd=Sum("quantidade"),
            receita=Coalesce(
                Sum(F("quantidade") * F("preco_unitario"), output_field=DEC),
                Value(0), output_field=DEC,
            ),
            pedidos=Count("pedido", distinct=True),
        )
        .order_by("-qtd", "produto__nome")
    )
    total_qtd = sum(l["qtd"] or 0 for l in linhas)
    total_receita = sum((l["receita"] or ZERO for l in linhas), ZERO)
    itens = [
        {
            "produto_id": l["produto_id"],
            "produto": l["produto__nome"],
            "tamanho": l["produto__tamanho"] or "",
            "categoria": l["produto__categoria__nome"] or "",
            "sku": l["produto__sku"] or "",
            "qtd": l["qtd"] or 0,
            "receita": l["receita"] or ZERO,
            "pedidos": l["pedidos"],
            "participacao": float(l["receita"] / total_receita) if total_receita else 0.0,
        }
        for l in linhas
    ]
    return {"itens": itens, "total_qtd": total_qtd, "total_receita": total_receita}


def produtos_csv(inicio: date, fim: date) -> HttpResponse:
    dados = produtos_vendidos(inicio, fim)
    return csv_response(
        f"produtos_vendidos_{inicio}_{fim}",
        ["produto", "tamanho", "categoria", "sku", "quantidade", "receita", "pedidos"],
        [[i["produto"], i["tamanho"], i["categoria"], i["sku"], i["qtd"], i["receita"], i["pedidos"]]
         for i in dados["itens"]],
    )


# --------------------------------------------------------------------------- #
# Estoque atual
# --------------------------------------------------------------------------- #
def _situacao(p: Produto) -> str:
    if p.quantidade_atual <= 0:
        return "esgotado"
    if p.quantidade_atual <= p.estoque_minimo:
        return "baixo"
    return "ok"


def estoque_atual(situacao: str | None = None, incluir_inativos: bool = False) -> dict:
    qs = Produto.objects.select_related("categoria").order_by("nome")
    if not incluir_inativos:
        qs = qs.filter(status=Produto.Status.ATIVO)
    if situacao == "baixo":
        qs = qs.filter(quantidade_atual__gt=0, quantidade_atual__lte=F("estoque_minimo"))
    elif situacao == "esgotado":
        qs = qs.filter(quantidade_atual__lte=0)
    produtos = list(qs)
    itens = [
        {
            "id": p.id,
            "nome": p.nome,
            "tamanho": p.tamanho or "",
            "categoria": p.categoria.nome if p.categoria else "",
            "sku": p.sku or "",
            "saldo": p.quantidade_atual,
            "minimo": p.estoque_minimo,
            "custo_unitario": p.custo_unitario,
            "preco_venda": p.preco_venda,
            "valor_em_estoque": p.valor_em_estoque,
            "situacao": _situacao(p),
            "url": p.get_absolute_url() if hasattr(p, "get_absolute_url") else "",
        }
        for p in produtos
    ]
    resumo = {"ok": 0, "baixo": 0, "esgotado": 0}
    for i in itens:
        resumo[i["situacao"]] += 1
    return {
        "itens": itens,
        "valor_total": sum((i["valor_em_estoque"] for i in itens), ZERO),
        "unidades": sum(i["saldo"] for i in itens),
        "resumo": resumo,
        "produtos": produtos,  # para a tela antiga
    }


def estoque_csv(situacao: str | None = None) -> HttpResponse:
    dados = estoque_atual(situacao)
    return csv_response(
        "estoque_atual",
        ["produto", "tamanho", "categoria", "saldo", "minimo", "valor_em_estoque", "situacao"],
        [[i["nome"], i["tamanho"], i["categoria"], i["saldo"], i["minimo"], i["valor_em_estoque"], i["situacao"]]
         for i in dados["itens"]],
    )


# --------------------------------------------------------------------------- #
# Clientes
# --------------------------------------------------------------------------- #
def clientes(recorrentes: bool = False, limite: int = 300):
    qs = (
        Cliente.objects.select_related("categoria")
        .annotate(
            qtd_pedidos=Count("pedidos", filter=~Q(pedidos__status__in=STATUS_IGNORADOS), distinct=True),
            gasto=Coalesce(
                Sum("pedidos__valor_total", filter=Q(pedidos__status__in=STATUS_RECEITA)),
                Value(0), output_field=DEC,
            ),
        )
        .order_by("-qtd_pedidos", "-gasto", "nome")
    )
    if recorrentes:
        qs = qs.filter(qtd_pedidos__gte=2)
    return qs[:limite]


def clientes_dict(recorrentes: bool = False) -> dict:
    lista = list(clientes(recorrentes))
    return {
        "itens": [
            {
                "id": c.id, "nome": c.nome, "email": c.email, "curso": c.curso,
                "categoria": c.categoria.nome if c.categoria else "",
                "pedidos": c.qtd_pedidos, "gasto": c.gasto,
                "url": c.get_absolute_url() if hasattr(c, "get_absolute_url") else "",
            }
            for c in lista
        ],
        "total": len(lista),
    }


def clientes_csv(recorrentes: bool = False) -> HttpResponse:
    return csv_response(
        "clientes",
        ["nome", "email", "curso", "categoria", "pedidos", "gasto"],
        [[i["nome"], i["email"], i["curso"], i["categoria"], i["pedidos"], i["gasto"]]
         for i in clientes_dict(recorrentes)["itens"]],
    )
