"""Números do painel. Usado pela tela antiga (``DashboardView``) e pela API
(``GET /api/dashboard/``), para os dois mostrarem exatamente a mesma coisa.

Definições (herdadas da tela antiga):
- **pedidos** no período: tudo menos rascunho e cancelado.
- **receita** no período: pedidos pagos, em separação, prontos ou entregues.
- **ticket médio**: receita / nº de pedidos que compõem a receita.
- **clientes novos**: clientes criados no período.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db import models
from django.db.models import Count, DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce, TruncDate, TruncMonth
from django.utils import timezone

from apps.catalogo.models import Produto
from apps.crm.models import Cliente
from apps.eventos.models import Evento
from apps.fornecedores.models import Fornecedor
from apps.tarefas.models import Tarefa
from apps.vendas.models import ItemPedido, Pedido

from ..models import RegistroAtividade
from .periodos import Periodo, preencher_serie, primeiro_dia_do_mes

DEC = DecimalField(max_digits=12, decimal_places=2)
ZERO = Decimal("0")
STATUS_RECEITA = [Pedido.Status.PAGO, Pedido.Status.SEPARACAO,
                  Pedido.Status.PRONTO, Pedido.Status.ENTREGUE]
STATUS_IGNORADOS = [Pedido.Status.RASCUNHO, Pedido.Status.CANCELADO]


def _soma(qs, campo="valor_total"):
    return qs.aggregate(t=Coalesce(Sum(campo), Value(0), output_field=DEC))["t"] or ZERO


def pedidos_validos(inicio: date, fim: date):
    return Pedido.objects.filter(data_compra__range=(inicio, fim)).exclude(
        status__in=STATUS_IGNORADOS
    )


def pedidos_com_receita(inicio: date, fim: date):
    return Pedido.objects.filter(
        data_compra__range=(inicio, fim), status__in=STATUS_RECEITA
    )


# --------------------------------------------------------------------------- #
# Totais e séries
# --------------------------------------------------------------------------- #
def totais(inicio: date, fim: date) -> dict:
    com_receita = pedidos_com_receita(inicio, fim)
    receita = _soma(com_receita)
    n_receita = com_receita.count()
    return {
        "receita": receita,
        "pedidos": pedidos_validos(inicio, fim).count(),
        "pedidos_com_receita": n_receita,
        "ticket_medio": (receita / n_receita) if n_receita else ZERO,
        "clientes_novos": Cliente.objects.filter(
            criado_em__date__range=(inicio, fim)
        ).count(),
    }


def _agrupar_por_tempo(qs, campo_data: str, granularidade: str, **agregacoes) -> dict:
    """``{data: {nome: valor}}``; em ``mes`` a chave é o dia 1 do mês."""
    campo = qs.model._meta.get_field(campo_data)
    eh_datetime = isinstance(campo, models.DateTimeField)
    if granularidade == "mes":
        qs = qs.annotate(_ponto=TruncMonth(campo_data))
    elif eh_datetime:
        qs = qs.annotate(_ponto=TruncDate(campo_data))
    else:
        # DateField puro: TruncDate quebra no SQLite (espera datetime).
        qs = qs.annotate(_ponto=F(campo_data))
    resultado = {}
    for linha in qs.values("_ponto").annotate(**agregacoes).order_by("_ponto"):
        ponto = linha["_ponto"]
        if hasattr(ponto, "date"):
            ponto = ponto.date()
        if granularidade == "mes":
            ponto = primeiro_dia_do_mes(ponto)
        resultado[ponto] = {k: linha[k] for k in agregacoes}
    return resultado


def _series_brutas(inicio: date, fim: date, granularidade: str) -> dict[str, list]:
    receita = _agrupar_por_tempo(
        pedidos_com_receita(inicio, fim), "data_compra", granularidade,
        valor=Coalesce(Sum("valor_total"), Value(0), output_field=DEC), qtd=Count("id"),
    )
    pedidos = _agrupar_por_tempo(
        pedidos_validos(inicio, fim), "data_compra", granularidade, qtd=Count("id"),
    )
    clientes = _agrupar_por_tempo(
        Cliente.objects.filter(criado_em__date__range=(inicio, fim)), "criado_em",
        granularidade, qtd=Count("id"),
    )
    serie_receita = preencher_serie(
        {k: v["valor"] for k, v in receita.items()}, inicio, fim, granularidade, ZERO
    )
    serie_n_receita = preencher_serie(
        {k: v["qtd"] for k, v in receita.items()}, inicio, fim, granularidade
    )
    return {
        "receita": serie_receita,
        "pedidos": preencher_serie(
            {k: v["qtd"] for k, v in pedidos.items()}, inicio, fim, granularidade
        ),
        "clientes_novos": preencher_serie(
            {k: v["qtd"] for k, v in clientes.items()}, inicio, fim, granularidade
        ),
        "ticket_medio": [
            (d, (r / n) if n else ZERO)
            for (d, r), (_, n) in zip(serie_receita, serie_n_receita)
        ],
    }


def series(periodo: Periodo) -> dict[str, list[dict]]:
    """``{nome: [{"data", "valor", "anterior"?}]}``. Com ``comparar``, o ponto
    ``i`` do período anterior é alinhado ao ponto ``i`` do atual."""
    atuais = _series_brutas(periodo.inicio, periodo.fim, periodo.granularidade)
    anteriores = None
    if periodo.comparar:
        ant = periodo.anterior
        anteriores = _series_brutas(ant.inicio, ant.fim, periodo.granularidade)

    saida = {}
    for nome, pontos in atuais.items():
        linhas = []
        for i, (data_ponto, valor) in enumerate(pontos):
            linha = {"data": data_ponto.isoformat(), "valor": valor}
            if anteriores is not None:
                serie_ant = anteriores[nome]
                linha["anterior"] = serie_ant[i][1] if i < len(serie_ant) else None
            linhas.append(linha)
        saida[nome] = linhas
    return saida


def _variacao(valor, anterior):
    if anterior in (None, 0, ZERO):
        return None
    return float((Decimal(valor) - Decimal(anterior)) / Decimal(anterior))


def kpis(periodo: Periodo, series_prontas: dict | None = None) -> dict:
    atual = totais(periodo.inicio, periodo.fim)
    anterior = totais(periodo.anterior.inicio, periodo.anterior.fim) if periodo.comparar else None
    series_prontas = series_prontas or series(periodo)
    saida = {}
    for nome in ("receita", "pedidos", "clientes_novos", "ticket_medio"):
        valor = atual[nome]
        valor_ant = anterior[nome] if anterior else None
        saida[nome] = {
            "valor": valor,
            "anterior": valor_ant,
            "variacao": _variacao(valor, valor_ant) if anterior else None,
            "serie": [p["valor"] for p in series_prontas[nome]],
        }
    return saida


# --------------------------------------------------------------------------- #
# Distribuições e rankings do período
# --------------------------------------------------------------------------- #
def distribuicao_status(inicio: date, fim: date) -> list[dict]:
    linhas = (
        Pedido.objects.filter(data_compra__range=(inicio, fim))
        .values("status")
        .annotate(qtd=Count("id"), valor=Coalesce(Sum("valor_total"), Value(0), output_field=DEC))
    )
    por_status = {l["status"]: l for l in linhas}
    return [
        {"status": valor, "rotulo": rotulo,
         "qtd": por_status.get(valor, {}).get("qtd", 0),
         "valor": por_status.get(valor, {}).get("valor", ZERO)}
        for valor, rotulo in Pedido.Status.choices
        if valor in por_status
    ]


def formas_pagamento(inicio: date, fim: date) -> list[dict]:
    rotulos = dict(Pedido.FormaPagamento.choices)
    linhas = (
        pedidos_com_receita(inicio, fim)
        .values("forma_pagamento")
        .annotate(qtd=Count("id"), valor=Coalesce(Sum("valor_total"), Value(0), output_field=DEC))
        .order_by("-valor")
    )
    return [
        {"forma": l["forma_pagamento"], "rotulo": rotulos.get(l["forma_pagamento"], l["forma_pagamento"] or "Não informada"),
         "qtd": l["qtd"], "valor": l["valor"]}
        for l in linhas
    ]


def top_produtos(inicio: date, fim: date, n: int = 5) -> list[dict]:
    linhas = (
        ItemPedido.objects.filter(pedido__data_compra__range=(inicio, fim))
        .exclude(pedido__status__in=STATUS_IGNORADOS)
        .values("produto__nome")
        .annotate(
            qtd=Sum("quantidade"),
            receita=Coalesce(
                Sum(F("quantidade") * F("preco_unitario"), output_field=DEC),
                Value(0), output_field=DEC,
            ),
        )
        .order_by("-qtd")[:n]
    )
    return [{"nome": l["produto__nome"], "qtd": l["qtd"], "receita": l["receita"]} for l in linhas]


# --------------------------------------------------------------------------- #
# Estado atual (não depende do período)
# --------------------------------------------------------------------------- #
def alertas() -> dict:
    hoje = timezone.localdate()
    return {
        "pedidos_aguardando": Pedido.objects.filter(status=Pedido.Status.AGUARDANDO).count(),
        "pedidos_retirada": Pedido.objects.filter(
            status__in=[Pedido.Status.SEPARACAO, Pedido.Status.PRONTO]
        ).count(),
        "produtos_baixo": Produto.objects.filter(
            status=Produto.Status.ATIVO, quantidade_atual__gt=0,
            quantidade_atual__lte=F("estoque_minimo"),
        ).count(),
        "produtos_esgotados": Produto.objects.filter(
            status=Produto.Status.ATIVO, quantidade_atual__lte=0
        ).count(),
        "tarefas_atrasadas": Tarefa.objects.filter(prazo__lt=hoje).exclude(
            status__in=[Tarefa.Status.CONCLUIDA, Tarefa.Status.CANCELADA]
        ).count(),
        "fornecedores_ativos": Fornecedor.objects.filter(status=Fornecedor.Status.ATIVO).count(),
        "clientes_total": Cliente.objects.count(),
        "valor_estoque": Produto.objects.aggregate(
            t=Coalesce(
                Sum(F("custo_unitario") * F("quantidade_atual"), output_field=DEC),
                Value(0), output_field=DEC,
            )
        )["t"] or ZERO,
    }


def minhas_tarefas(usuario, n: int = 6):
    return (
        Tarefa.objects.filter(responsavel=usuario)
        .exclude(status__in=[Tarefa.Status.CONCLUIDA, Tarefa.Status.CANCELADA])
        .order_by(F("prazo").asc(nulls_last=True))[:n]
    )


def atividades(n: int = 12):
    return RegistroAtividade.objects.select_related("usuario")[:n]


def proximos_eventos(n: int = 4):
    return (
        Evento.objects.filter(
            data__gte=timezone.localdate(),
            status__in=[Evento.Status.PLANEJAMENTO, Evento.Status.CONFIRMADO],
        ).order_by("data")[:n]
    )


# --------------------------------------------------------------------------- #
# Payload completo da API
# --------------------------------------------------------------------------- #
def _tarefa_dict(t: Tarefa) -> dict:
    return {
        "id": t.id, "titulo": t.titulo, "prazo": t.prazo, "prioridade": t.prioridade,
        "prioridade_rotulo": t.get_prioridade_display(), "status": t.status,
        "status_rotulo": t.get_status_display(), "atrasada": t.atrasada,
        "url": f"/tarefas/{t.id}",
    }


def _evento_dict(e: Evento) -> dict:
    return {
        "id": e.id, "nome": e.nome, "data": e.data, "tipo": e.tipo,
        "tipo_rotulo": e.get_tipo_display(), "status": e.status,
        "status_rotulo": e.get_status_display(),
        "ingressos_vendidos": e.ingressos_vendidos,
        "receita_total": e.receita_total,
        "url": f"/eventos/{e.id}",
    }


def montar(periodo: Periodo, usuario) -> dict:
    from ..serializers import RegistroAtividadeSerializer

    series_prontas = series(periodo)
    return {
        "periodo": periodo.como_dict(),
        "kpis": kpis(periodo, series_prontas),
        "series": series_prontas,
        "status_pedidos": distribuicao_status(periodo.inicio, periodo.fim),
        "formas_pagamento": formas_pagamento(periodo.inicio, periodo.fim),
        "top_produtos": top_produtos(periodo.inicio, periodo.fim),
        "alertas": alertas(),
        "minhas_tarefas": [_tarefa_dict(t) for t in minhas_tarefas(usuario)],
        "proximos_eventos": [_evento_dict(e) for e in proximos_eventos()],
        "atividades": RegistroAtividadeSerializer(atividades(), many=True).data,
    }
