"""Período de análise compartilhado por dashboard e relatórios.

Parâmetros aceitos (query string):
    periodo = hoje | 7d | 30d | semestre | ano | custom   (padrão: 30d)
    inicio, fim = AAAA-MM-DD (só com periodo=custom)
    comparar = 1 | true  → também calcula o período anterior de mesma duração

Regras:
- ``granularidade`` é ``dia`` até LIMITE_DIA dias e ``mes`` acima disso. Quem
  decide é o servidor, e o valor volta no payload.
- ``preencher_serie`` faz zero-fill: todo ponto do eixo existe, mesmo sem
  venda, para a escala de tempo nunca ser distorcida no gráfico.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from django.utils import timezone

PRESETS = {
    "hoje": "Hoje",
    "7d": "Últimos 7 dias",
    "30d": "Últimos 30 dias",
    "semestre": "Este semestre",
    "ano": "Este ano",
    "custom": "Período personalizado",
}
PADRAO = "30d"
LIMITE_DIA = 120           # acima disso a série vira mensal
LIMITE_DIAS_CUSTOM = 366 * 3


def intervalo_preset(chave: str, hoje: date | None = None) -> tuple[date, date]:
    """Mesma regra da tela antiga (``_intervalo`` de ``nucleo/views.py``)."""
    hoje = hoje or timezone.localdate()
    if chave == "hoje":
        return hoje, hoje
    if chave == "7d":
        return hoje - timedelta(days=7), hoje
    if chave == "ano":
        return hoje.replace(month=1, day=1), hoje
    if chave == "semestre":
        mes_inicio = 1 if hoje.month <= 6 else 7
        return hoje.replace(month=mes_inicio, day=1), hoje
    return hoje - timedelta(days=30), hoje


@dataclass(frozen=True)
class Periodo:
    chave: str
    rotulo: str
    inicio: date
    fim: date
    comparar: bool = False

    @property
    def dias(self) -> int:
        return (self.fim - self.inicio).days + 1

    @property
    def granularidade(self) -> str:
        return "dia" if self.dias <= LIMITE_DIA else "mes"

    @property
    def anterior_fim(self) -> date:
        return self.inicio - timedelta(days=1)

    @property
    def anterior_inicio(self) -> date:
        return self.anterior_fim - timedelta(days=self.dias - 1)

    @property
    def anterior(self) -> "Periodo":
        return Periodo(
            chave=self.chave, rotulo="Período anterior",
            inicio=self.anterior_inicio, fim=self.anterior_fim, comparar=False,
        )

    def como_dict(self) -> dict:
        return {
            "chave": self.chave,
            "rotulo": self.rotulo,
            "inicio": self.inicio.isoformat(),
            "fim": self.fim.isoformat(),
            "dias": self.dias,
            "granularidade": self.granularidade,
            "comparar": self.comparar,
            "anterior": {
                "inicio": self.anterior_inicio.isoformat(),
                "fim": self.anterior_fim.isoformat(),
            },
        }


def _parse_data(valor) -> date | None:
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def resolver(params, hoje: date | None = None) -> Periodo:
    """``params`` é qualquer mapping (``request.GET``/``query_params``)."""
    hoje = hoje or timezone.localdate()
    chave = str(params.get("periodo") or PADRAO)
    if chave not in PRESETS:
        chave = PADRAO
    comparar = str(params.get("comparar", "")).lower() in ("1", "true", "sim")

    if chave == "custom":
        inicio, fim = _parse_data(params.get("inicio")), _parse_data(params.get("fim"))
        if inicio is None and fim is None:
            chave = PADRAO
        else:
            inicio = inicio or fim
            fim = fim or inicio
            if inicio > fim:
                inicio, fim = fim, inicio
            if (fim - inicio).days + 1 > LIMITE_DIAS_CUSTOM:
                inicio = fim - timedelta(days=LIMITE_DIAS_CUSTOM - 1)
            rotulo = f"{inicio:%d/%m/%Y} a {fim:%d/%m/%Y}"
            return Periodo("custom", rotulo, inicio, fim, comparar)

    inicio, fim = intervalo_preset(chave, hoje)
    return Periodo(chave, PRESETS[chave], inicio, fim, comparar)


def primeiro_dia_do_mes(d: date) -> date:
    return d.replace(day=1)


def _proximo_mes(d: date) -> date:
    return date(d.year + (d.month == 12), 1 if d.month == 12 else d.month + 1, 1)


def eixo(inicio: date, fim: date, granularidade: str) -> list[date]:
    """Todos os pontos do intervalo: um por dia, ou o dia 1 de cada mês."""
    pontos = []
    if granularidade == "mes":
        atual = primeiro_dia_do_mes(inicio)
        while atual <= fim:
            pontos.append(atual)
            atual = _proximo_mes(atual)
        return pontos
    atual = inicio
    while atual <= fim:
        pontos.append(atual)
        atual += timedelta(days=1)
    return pontos


def preencher_serie(agregado: dict, inicio: date, fim: date, granularidade: str,
                    vazio=0) -> list[tuple[date, object]]:
    """Zero-fill: ``agregado`` mapeia data (dia ou dia 1 do mês) → valor."""
    return [(ponto, agregado.get(ponto, vazio)) for ponto in eixo(inicio, fim, granularidade)]
