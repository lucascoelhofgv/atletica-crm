"""Gravação das planilhas de Esportes e o resumo orçado x realizado.

A planilha é a fonte da verdade. Sincronizar cria o que é novo, atualiza o que
mudou e remove o que saiu da planilha, mas só dentro do que aquela planilha
cobre (o ano do orçamento; os semestres que aparecem nos treinos). Assim uma
planilha "Treinos 26.2" não apaga os treinos de 26.1 e vice-versa.
"""

from __future__ import annotations

from collections import Counter

from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone

from apps.nucleo.models import registrar_atividade

from . import importador
from .models import (
    ZERO, Modalidade, OrcamentoModalidade, Sessao, meses_do_semestre, semestre_de,
)

MAX_AVISOS = 50


def _modalidade(esporte, naipe, cache):
    chave = (esporte, naipe)
    if chave not in cache:
        cache[chave], _ = Modalidade.objects.get_or_create(esporte=esporte, naipe=naipe)
    return cache[chave]


# --------------------------------------------------------------------------- #
# Orçamento
# --------------------------------------------------------------------------- #
def previa_orcamento(grade) -> dict:
    dados = importador.analisar_orcamento(grade)
    semestres = sorted({(s["ano"], s["semestre"]) for m in dados["modalidades"] for s in m["semestres"]})
    total = sum(
        s["treinos_previstos"] * (m["custo_quadra_hora"] + m["custo_treinador_treino"])
        + s["jogos_previstos"] * m["custo_treinador_jogo"]
        for m in dados["modalidades"] for s in m["semestres"]
    )
    return {
        "modalidades": len(dados["modalidades"]),
        "semestres": [f"{a}.{s}" for a, s in semestres],
        "total_previsto": total,
        "avisos": dados["avisos"][:MAX_AVISOS],
    }


@transaction.atomic
def importar_orcamento(grade, usuario=None) -> dict:
    dados = importador.analisar_orcamento(grade)
    if not dados["modalidades"]:
        raise ValueError(dados["avisos"][0] if dados["avisos"] else "Planilha de orçamento vazia.")

    cache, vistos, anos = {}, set(), set()
    criados = atualizados = 0
    for m in dados["modalidades"]:
        mod = _modalidade(m["esporte"], m["naipe"], cache)
        for campo in ("dia_semana", "horario_inicio", "horario_fim", "local"):
            if m[campo]:
                setattr(mod, campo, m[campo])
        mod.save()
        for s in m["semestres"]:
            anos.add(s["ano"])
            _, novo = OrcamentoModalidade.objects.update_or_create(
                modalidade=mod, ano=s["ano"], semestre=s["semestre"],
                defaults={
                    "custo_quadra_hora": m["custo_quadra_hora"],
                    "custo_treinador_treino": m["custo_treinador_treino"],
                    "custo_treinador_jogo": m["custo_treinador_jogo"],
                    "treinos_previstos": s["treinos_previstos"],
                    "jogos_previstos": s["jogos_previstos"],
                },
            )
            vistos.add((mod.pk, s["ano"], s["semestre"]))
            if novo:
                criados += 1
            else:
                atualizados += 1

    removidos = 0
    for orc in OrcamentoModalidade.objects.filter(ano__in=anos):
        if (orc.modalidade_id, orc.ano, orc.semestre) not in vistos:
            orc.delete()
            removidos += 1

    registrar_atividade(usuario, "sincronizou orçamento de Esportes",
                        f"{len(dados['modalidades'])} modalidade(s)")
    return {
        "modalidades": len(dados["modalidades"]),
        "criados": criados, "atualizados": atualizados, "removidos": removidos,
        "avisos": dados["avisos"][:MAX_AVISOS],
    }


# --------------------------------------------------------------------------- #
# Treinos
# --------------------------------------------------------------------------- #
def previa_treinos(grades) -> dict:
    dados = importador.analisar_treinos(grades)
    sessoes = dados["sessoes"]
    return {
        "esportes": dados["esportes"],
        "treinos": sum(1 for s in sessoes if s["tipo"] == "treino"),
        "jogos": sum(1 for s in sessoes if s["tipo"] == "jogo"),
        "custo_total": sum(s["custo"] for s in sessoes),
        "periodo": (
            [min(s["data"] for s in sessoes).isoformat(), max(s["data"] for s in sessoes).isoformat()]
            if sessoes else []
        ),
        "avisos": dados["avisos"][:MAX_AVISOS],
    }


@transaction.atomic
def importar_treinos(grades, usuario=None) -> dict:
    dados = importador.analisar_treinos(grades)
    if not dados["sessoes"]:
        raise ValueError("Não achei nenhum treino ou jogo na planilha (blocos com 'Data' e 'Equipe').")

    cache, vistas = {}, set()
    criados = atualizados = 0
    for s in dados["sessoes"]:
        mod = _modalidade(s["esporte"], s["naipe"], cache)
        sessao, novo = Sessao.objects.update_or_create(
            modalidade=mod, tipo=s["tipo"], data=s["data"],
            defaults={k: s[k] for k in (
                "confirmada", "teve_tecnico", "teve_quadra", "custo_tecnico",
                "custo_quadra", "custo", "observacao", "origem")},
        )
        vistas.add(sessao.pk)
        if novo:
            criados += 1
        else:
            atualizados += 1

    # Remove o que saiu da planilha, só nos esportes e semestres que ela cobre.
    alcance = {(s["esporte"], s["data"].year, semestre_de(s["data"])) for s in dados["sessoes"]}
    filtro = Q(pk__in=[])
    for esporte, ano, sem in alcance:
        meses = meses_do_semestre(sem)
        filtro |= Q(modalidade__esporte=esporte, data__year=ano,
                    data__month__gte=meses.start, data__month__lt=meses.stop)
    removidos, _ = Sessao.objects.filter(filtro).exclude(pk__in=vistas).delete()

    registrar_atividade(usuario, "sincronizou treinos de Esportes",
                        f"{len(dados['sessoes'])} treino(s) e jogo(s)")
    return {
        "criados": criados, "atualizados": atualizados, "removidos": removidos,
        "avisos": dados["avisos"][:MAX_AVISOS],
    }


# --------------------------------------------------------------------------- #
# Resumo para o painel
# --------------------------------------------------------------------------- #
def semestres_disponiveis() -> list[tuple[int, int]]:
    pares = set(OrcamentoModalidade.objects.values_list("ano", "semestre"))
    for d in Sessao.objects.dates("data", "month"):
        pares.add((d.year, semestre_de(d)))
    return sorted(pares, reverse=True)


def semestre_padrao() -> tuple[int, int]:
    """O semestre mais recente que já tem treino lançado; sem treino nenhum, o
    mais recente com orçamento; sem nada, o de hoje."""
    ultima = Sessao.objects.aggregate(m=Max("data"))["m"]
    if ultima:
        return ultima.year, semestre_de(ultima)
    disponiveis = semestres_disponiveis()
    if disponiveis:
        return disponiveis[0]
    hoje = timezone.localdate()
    return hoje.year, semestre_de(hoje)


def _mais_comum(valores):
    valores = [v for v in valores if v]
    return Counter(valores).most_common(1)[0][0] if valores else None


def _percentual(parte, todo):
    return float(parte / todo) if todo else None


def resumo(ano: int | None = None, semestre: int | None = None) -> dict:
    if not ano or semestre not in (1, 2):
        ano, semestre = semestre_padrao()
    meses = meses_do_semestre(semestre)

    sessoes = list(
        Sessao.objects.filter(data__year=ano, data__month__gte=meses.start,
                              data__month__lt=meses.stop).select_related("modalidade")
    )
    orcamentos = {
        o.modalidade_id: o
        for o in OrcamentoModalidade.objects.filter(ano=ano, semestre=semestre).select_related("modalidade")
    }
    por_modalidade: dict[int, list] = {}
    for s in sessoes:
        por_modalidade.setdefault(s.modalidade_id, []).append(s)

    ids = set(orcamentos) | set(por_modalidade)
    modalidades = Modalidade.objects.filter(pk__in=ids)

    linhas = []
    for mod in modalidades:
        orc = orcamentos.get(mod.pk)
        lista = por_modalidade.get(mod.pk, [])
        treinos = [s for s in lista if s.tipo == Sessao.Tipo.TREINO]
        jogos = [s for s in lista if s.tipo == Sessao.Tipo.JOGO]
        realizado = sum((s.custo for s in lista), ZERO)
        orcado = orc.total_previsto if orc else ZERO
        linhas.append({
            "id": mod.pk,
            "nome": mod.nome,
            "esporte": mod.esporte,
            "naipe": mod.naipe,
            "local": mod.local,
            "dia_semana": mod.dia_semana,
            "tem_orcamento": orc is not None,
            "tem_registros": bool(lista),
            "orcado": orcado,
            "realizado": realizado,
            "diferenca": orcado - realizado,
            "uso": _percentual(realizado, orcado),
            "realizado_tecnico": sum((s.custo_tecnico for s in lista if s.teve_tecnico), ZERO),
            "realizado_quadra": sum((s.custo_quadra for s in lista if s.teve_quadra), ZERO),
            "treinos_previstos": orc.treinos_previstos if orc else 0,
            "treinos_registrados": len(treinos),
            "treinos_confirmados": sum(1 for s in treinos if s.confirmada),
            "treinos_cancelados": sum(1 for s in treinos if not s.confirmada),
            "jogos_previstos": orc.jogos_previstos if orc else 0,
            "jogos_registrados": len(jogos),
            "valor_quadra_orcado": orc.custo_quadra_hora if orc else None,
            "valor_quadra_real": _mais_comum(s.custo_quadra for s in treinos),
            "valor_tecnico_orcado": orc.custo_treinador_treino if orc else None,
            "valor_tecnico_real": _mais_comum(s.custo_tecnico for s in treinos),
        })
    linhas.sort(key=lambda l: (-l["realizado"], -l["orcado"], l["nome"]))

    por_mes = []
    for mes in meses:
        do_mes = [s for s in sessoes if s.data.month == mes]
        por_mes.append({
            "mes": f"{ano}-{mes:02d}",
            "realizado": sum((s.custo for s in do_mes), ZERO),
            "tecnico": sum((s.custo_tecnico for s in do_mes if s.teve_tecnico), ZERO),
            "quadra": sum((s.custo_quadra for s in do_mes if s.teve_quadra), ZERO),
            "treinos": sum(1 for s in do_mes if s.tipo == Sessao.Tipo.TREINO and s.confirmada),
            "jogos": sum(1 for s in do_mes if s.tipo == Sessao.Tipo.JOGO),
        })

    orcado_total = sum((l["orcado"] for l in linhas), ZERO)
    realizado_total = sum((l["realizado"] for l in linhas), ZERO)
    datas = [s.data for s in sessoes]

    from apps.nucleo.models import FontePlanilha

    ultima = FontePlanilha.objects.filter(
        destino__in=[FontePlanilha.Destino.ESPORTES_ORCAMENTO, FontePlanilha.Destino.ESPORTES_TREINOS]
    ).aggregate(m=Max("ultima_sincronizacao"))["m"]

    return {
        "ano": ano,
        "semestre": semestre,
        "semestres_disponiveis": [{"ano": a, "semestre": s} for a, s in semestres_disponiveis()],
        "ultima_sincronizacao": ultima,
        "primeiro_registro": min(datas) if datas else None,
        "ultimo_registro": max(datas) if datas else None,
        "totais": {
            "orcado": orcado_total,
            "realizado": realizado_total,
            "diferenca": orcado_total - realizado_total,
            "uso": _percentual(realizado_total, orcado_total),
            "treinos_previstos": sum(l["treinos_previstos"] for l in linhas),
            "treinos_registrados": sum(l["treinos_registrados"] for l in linhas),
            "treinos_confirmados": sum(l["treinos_confirmados"] for l in linhas),
            "treinos_cancelados": sum(l["treinos_cancelados"] for l in linhas),
            "jogos_previstos": sum(l["jogos_previstos"] for l in linhas),
            "jogos_registrados": sum(l["jogos_registrados"] for l in linhas),
        },
        "modalidades": linhas,
        "por_mes": por_mes,
    }
