"""Leitura das planilhas de Esportes, sem banco."""

from datetime import date, time
from decimal import Decimal

from apps.esportes import importador as imp

from . import planilhas


def test_modalidade_e_equipe_viram_esporte_e_naipe():
    assert imp.separar_modalidade("Hand Feminino") == ("Handebol", "fem")
    assert imp.separar_modalidade("Volei Masculino") == ("Vôlei", "masc")
    assert imp.separar_modalidade("Bateria") == ("Bateria", "misto")
    assert imp.separar_equipe("Masc ") == ("masc", "")
    assert imp.separar_equipe("Fem Atcup") == ("fem", "Atcup")
    assert imp.separar_equipe("Torcida") == (None, "Torcida")
    assert imp.esporte_canonico("VÔLEI") == "Vôlei"


def test_dinheiro_aceita_os_dois_jeitos_de_escrever():
    assert imp._dinheiro("86,5") == Decimal("86.5")
    assert imp._dinheiro("1.300,00") == Decimal("1300.00")
    assert imp._dinheiro("R$ 200") == Decimal("200")
    assert imp._dinheiro("86.5") == Decimal("86.5")
    assert imp._dinheiro("1.300") == Decimal("1300")
    assert imp._dinheiro("") is None


def test_orcamento_le_a_tabela_e_ignora_o_resto_da_aba():
    dados = imp.analisar_orcamento(planilhas.orcamento())

    assert dados["avisos"] == []
    nomes = [(m["esporte"], m["naipe"]) for m in dados["modalidades"]]
    assert nomes == [("Bateria", "misto"), ("Basquete", "fem"), ("Futsal", "masc"), ("Handebol", "fem")]

    basquete = dados["modalidades"][1]
    assert basquete["local"] == "Hebraica"
    assert basquete["horario_inicio"] == time(21, 30)
    assert basquete["custo_quadra_hora"] == Decimal("350")
    assert basquete["custo_treinador_treino"] == Decimal("125")
    assert basquete["custo_treinador_jogo"] == Decimal("160")
    assert basquete["semestres"] == [
        {"ano": 2026, "semestre": 1, "treinos_previstos": 24, "jogos_previstos": 3},
        {"ano": 2026, "semestre": 2, "treinos_previstos": 24, "jogos_previstos": 3},
    ]
    assert dados["modalidades"][0]["custo_quadra_hora"] == Decimal("86.5")


def test_orcamento_sem_cabecalho_avisa():
    dados = imp.analisar_orcamento([["qualquer coisa"]])

    assert dados["modalidades"] == []
    assert "Modalidade" in dados["avisos"][0]


def test_treinos_le_os_blocos_e_o_custo_de_cada_um():
    dados = imp.analisar_treinos(planilhas.treinos())
    sessoes = {(s["esporte"], s["naipe"], s["tipo"], s["data"]): s for s in dados["sessoes"]}

    assert dados["esportes"] == ["Futsal", "Handebol"]
    assert len(sessoes) == 8

    # Treino feminino sem quadra: só o técnico.
    s = sessoes[("Futsal", "fem", "treino", date(2026, 2, 23))]
    assert (s["teve_tecnico"], s["teve_quadra"], s["custo"]) == (True, False, Decimal("130"))
    # "Masc " com espaço e "masc" minúsculo contam como masculino.
    assert sessoes[("Futsal", "masc", "treino", date(2026, 2, 24))]["custo"] == Decimal("270")
    cancelado = sessoes[("Futsal", "masc", "treino", date(2026, 2, 26))]
    assert (cancelado["confirmada"], cancelado["custo"]) == (False, Decimal("0"))
    # Bloco de março colado no de fevereiro também é lido.
    atcup = sessoes[("Futsal", "fem", "treino", date(2026, 3, 2))]
    assert atcup["observacao"] == "Atcup"
    # Jogo usa o valor do técnico de jogo e não paga quadra.
    jogo = sessoes[("Futsal", "masc", "jogo", date(2026, 3, 15))]
    assert (jogo["custo_tecnico"], jogo["custo_quadra"], jogo["custo"]) == (
        Decimal("125"), Decimal("0"), Decimal("125"))
    # Linha em branco no meio do bloco não esconde o jogo de baixo.
    amistoso = sessoes[("Futsal", "masc", "jogo", date(2026, 3, 29))]
    assert amistoso["observacao"] == "Amistoso"
    # Quadra com valor por naipe.
    assert sessoes[("Handebol", "fem", "treino", date(2026, 8, 10))]["custo"] == Decimal("280")
    assert sessoes[("Handebol", "masc", "treino", date(2026, 8, 11))]["custo"] == Decimal("300")


def test_treinos_avisam_o_que_ficou_de_fora():
    avisos = imp.analisar_treinos(planilhas.treinos())["avisos"]

    assert any("FUTSAL L11" in a and "sem data" in a for a in avisos)
    assert any("FUTSAL B16" in a and "repetido" in a for a in avisos)
    assert any("FUTSAL B17" in a for a in avisos)
    assert len(avisos) == 3


def test_aba_sem_blocos_vira_aviso():
    dados = imp.analisar_treinos({"RASCUNHO": [["nada aqui"]]})

    assert dados["sessoes"] == []
    assert any("RASCUNHO" in a for a in dados["avisos"])
