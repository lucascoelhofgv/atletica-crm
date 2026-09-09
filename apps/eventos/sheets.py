"""Exporta as FESTAS para a aba 'Festas' da planilha do Google configurada.

Uma linha por festa, com receita, custo, resultado e indicadores — pronto para
análise ano a ano (Jungle 2024/2025/2026, FRAT HOUSE...).
"""

from apps.nucleo.sheets import _escrever_aba, abrir_planilha

from .models import Evento

CABECALHO = [
    "Festa", "Data", "Local", "Status", "Capacidade",
    "Ingressos previstos", "Ingressos vendidos", "Público estimado",
    "Receita ingressos (R$)", "Receita extra (R$)", "Receita total (R$)",
    "Custo total (R$)", "Custo pago (R$)", "Resultado (R$)", "Margem (%)",
    "Ticket médio (R$)", "Custo por pessoa (R$)", "Breakeven (ingressos)",
]


def _linha(ev: Evento):
    def money(v):
        return round(float(v), 2) if v is not None else ""

    margem = ev.margem
    return [
        ev.nome,
        ev.data.strftime("%d/%m/%Y") if ev.data else "",
        ev.local,
        ev.get_status_display(),
        ev.capacidade or "",
        ev.ingressos_previstos,
        ev.ingressos_vendidos,
        ev.publico_estimado,
        money(ev.receita_ingressos),
        money(ev.receita_extra),
        money(ev.receita_total),
        money(ev.custo_total),
        money(ev.custo_pago),
        money(ev.resultado),
        round(float(margem) * 100, 1) if margem is not None else "",
        money(ev.ticket_medio),
        money(ev.custo_por_pessoa),
        ev.breakeven_ingressos if ev.breakeven_ingressos is not None else "",
    ]


def exportar_festas(apenas_festas=True):
    """Escreve a aba 'Festas'. Retorna a quantidade de eventos exportados."""
    planilha = abrir_planilha()

    qs = Evento.objects.prefetch_related("lotes", "custos", "receitas")
    if apenas_festas:
        qs = qs.filter(tipo=Evento.Tipo.FESTA)
    eventos = list(qs.order_by("data"))

    _escrever_aba(planilha, "Festas", CABECALHO, [_linha(e) for e in eventos])
    return len(eventos)
