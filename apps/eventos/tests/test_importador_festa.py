from decimal import Decimal

import pytest

from apps.eventos.importador_festa import analisar, criar_festa
from apps.eventos.models import CustoEvento, Evento, LoteIngresso

pytestmark = pytest.mark.django_db

# Um recorte real da planilha Jungle/FRAT: dois painéis lado a lado na mesma
# linha (Lotes à esquerda, Custos Variáveis à direita começando na coluna 6),
# que é exatamente o formato que trava um parser ingênuo de "primeira célula
# de cada coluna".
GRID = [
    ["jungle 26", "Lotes oficiais", "Quantidade", "Valor", "Total"],
    ["", "Promocional", "12", "R$85,00", "R$1.020,00"],
    ["", "1º Lote", "101", "R$95,00", "R$9.595,00"],
    ["", "TOTAL", "113", "", "R$10.615,00"],
    [""],
    ["", "Custos Fixos", "Quantidade", "Valor unitario", "Valor total", "",
     "", "Custos Variáveis"],
    ["", "Local", "1", "R$4.500,00", "R$4.500,00", "", "", "Item", "ML", "ml/pessoa",
     "Qtd/pessoa", "Quantidade Real", "Quantidade Final", "Valor unitário", "Valor total"],
    ["", "DJ Thurrar", "1", "R$800,00", "R$800,00", "", "", "Água", "1.500,00", "425,53",
     "X", "X", "30", "$1,90", "R$ 57,00"],
    ["", "TOTAL", "", "", "R$5.300,00"],
]


def test_analisar_separa_lotes_e_os_dois_tipos_de_custo():
    dados = analisar(GRID)

    assert [l["nome"] for l in dados["lotes"]] == ["Promocional", "1º Lote"]
    assert dados["lotes"][0] == {
        "nome": "Promocional", "quantidade": 12, "valor_unitario": Decimal("85.00"),
    }

    fixos = [c for c in dados["custos"] if c["tipo"] == "fixo"]
    variaveis = [c for c in dados["custos"] if c["tipo"] == "variavel"]
    assert {c["item"] for c in fixos} == {"Local", "DJ Thurrar"}
    assert fixos[0]["valor_unitario"] == Decimal("4500.00")
    # o painel de custos variáveis, à direita na mesma linha, não pode vazar
    # números do painel de custos fixos (era o bug do parser antigo)
    assert {c["item"] for c in variaveis} == {"Água"}
    agua = variaveis[0]
    assert agua["quantidade"] == 30
    assert agua["valor_unitario"] == Decimal("1.90")


def test_criar_festa_grava_evento_lotes_e_custos():
    dados = analisar(GRID)
    ev = criar_festa(dados, nome="FRAT HOUSE 2026", data="2026-08-15",
                     local="Vale das Palmeiras", capacidade=300, staff=20)

    assert ev.tipo == Evento.Tipo.FESTA
    assert LoteIngresso.objects.filter(evento=ev).count() == 2
    assert CustoEvento.objects.filter(evento=ev).count() == 3  # 2 fixos + 1 variável
    assert ev.receita_ingressos == Decimal("85.00") * 12 + Decimal("95.00") * 101
    assert ev.custo_total == Decimal("4500.00") + Decimal("800.00") + Decimal("1.90") * 30
    assert ev.resultado == ev.receita_ingressos - ev.custo_total
