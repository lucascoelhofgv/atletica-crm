"""Lógica de eventos compartilhada pela tela antiga e pela API."""

from django.db.models import Q

from apps.nucleo.models import registrar_atividade

from .models import Evento


def buscar(qs, termo: str):
    termo = (termo or "").strip()
    if not termo:
        return qs
    return qs.filter(Q(nome__icontains=termo) | Q(local__icontains=termo))


def url_spa(e: Evento) -> str:
    return f"/eventos/{e.pk}"


def registrar(usuario, verbo: str, e: Evento, descricao: str = ""):
    registrar_atividade(usuario, verbo, e.nome, descricao, url=url_spa(e))


def resumo_financeiro(e: Evento) -> dict:
    """Empacota as propriedades de P&L do modelo num dict serializável."""
    return {
        "orcamento_previsto": e.orcamento_previsto,
        "ingressos_previstos": e.ingressos_previstos,
        "ingressos_vendidos": e.ingressos_vendidos,
        "receita_ingressos": e.receita_ingressos,
        "receita_ingressos_prevista": e.receita_ingressos_prevista,
        "receita_extra": e.receita_extra,
        "receita_total": e.receita_total,
        "custo_total": e.custo_total,
        "custo_pago": e.custo_pago,
        "custo_a_pagar": e.custo_a_pagar,
        "resultado": e.resultado,
        "margem": float(e.margem) if e.margem is not None else None,
        "publico_estimado": e.publico_estimado,
        "custo_por_pessoa": e.custo_por_pessoa,
        "ticket_medio": e.ticket_medio,
        "breakeven_ingressos": e.breakeven_ingressos,
    }
