"""Grades falsas no formato das planilhas reais de Esportes.

Copiam a disposição (células, blocos, ruído) das planilhas "Orçamento
Atlética para 2026" e "Treinos 26.1", sem os dados reais: os nomes dos atletas
não entram no repositório.
"""

import re


def grade(celulas: dict) -> list[list[str]]:
    """{'B2': 'Modalidade', ...} -> matriz de strings, como o sheets devolve."""
    pos = {}
    for coord, valor in celulas.items():
        m = re.match(r"([A-Z]+)(\d+)$", coord)
        col = 0
        for letra in m.group(1):
            col = col * 26 + ord(letra) - 64
        pos[(int(m.group(2)) - 1, col - 1)] = str(valor)
    linhas = max(r for r, _ in pos) + 1
    colunas = max(c for _, c in pos) + 1
    g = [[""] * colunas for _ in range(linhas)]
    for (r, c), v in pos.items():
        g[r][c] = v
    return g


def linha(numero, inicio, valores):
    """Valores em sequência a partir da coluna ``inicio`` na linha ``numero``."""
    col = ord(inicio) - 64
    saida = {}
    for i, v in enumerate(valores):
        if v is None:
            continue
        saida[f"{chr(64 + col + i)}{numero}"] = v
    return saida


CABECALHO_ORCAMENTO = [
    "Modalidade", "Dia", "Início", "Término", "Local", "Custo Aluguel 1h",
    "Custo Treinador 1h/Treino", "QTD Treinos 2026.1", "QTD Jogos 2026.1",
    "Custo Treinador 1h/Jogo", "Total 1º semestre", "QTD Treinos 2026.2",
    "QTD Jogos 2026.2", "Total 2º semestre", "Total 2026",
]


def orcamento():
    c = {"B1": "Treinos"}
    c.update(linha(2, "B", CABECALHO_ORCAMENTO))
    c.update(linha(3, "B", ["Bateria", "Terça", "18:00", "19:00", "Espaço Ipiranga",
                            "86,5", "0", "10", "0", "0", "865", "10", "0", "865", "1730"]))
    c.update(linha(4, "B", ["Basquete Feminino", "Terça", "21:30", "22:30", "Hebraica",
                            "350", "125", "24", "3", "160", "11880", "24", "3", "11880", "23760"]))
    c.update(linha(5, "B", ["Futsal Masculino", "Segunda", "21:00", "22:00", "Casa do Minho",
                            "200", "100", "24", "4", "150", "7800", "24", "4", "7800", "15600"]))
    c.update(linha(6, "B", ["Hand Feminino", "Quinta", "21:00", "22:00", "Casa do Minho",
                            "200", "100", "24", "3", "100", "7500", "24", "3", "7500", "15000"]))
    c.update({"L7": "35445", "O7": "35445", "P7": "70890"})  # linha de total
    # Rascunho e lista de atletas mais abaixo: tem de ser ignorado.
    c.update({"J14": "Real", "C29": "ATLETAS 2026", "C31": "Atletas FGV EBAPE", "C32": "Nome",
              "C33": "Fulano de Tal"})
    return grade(c)


def aba_futsal():
    """Futsal: técnico R$ 130 e quadra única R$ 140; jogos com técnico R$ 125."""
    c = {"B3": "Custos dos treinos", "F3": "Treinos", "L3": "Custos dos jogos"}
    c.update(linha(4, "B", ["Custo", "Descrição", "Valor"]))
    c.update(linha(4, "L", ["Custo", "Descrição", "Valor"]))
    c.update(linha(5, "B", ["Técnico", "Fábio", "130"]))
    c.update(linha(5, "L", ["Técnico", "Fábio ", "125"]))
    c.update(linha(6, "B", ["Quadra", "Jc2", "140"]))
    c.update({"B8": "Fevereiro", "H8": "Pagamento dos treinos (fev)", "L8": "MARÇO"})
    c.update(linha(9, "B", ["Data", "Equipe", "Confirmado", "Técnico", "Quadra"]))
    c.update(linha(9, "L", ["Data", "Equipe", "Confirmado", "Técnico"]))
    c.update(linha(10, "B", ["23/02/2026", "Fem", "Sim", "Sim", "Não"]))
    c.update(linha(10, "L", ["15/03/2026", "Masc", "Sim", "Sim", None, "Técnico"]))
    c.update(linha(11, "B", ["24/02/2026", "Masc ", "Sim", "Sim", "Sim"]))
    c.update(linha(11, "L", ["0", "Fem", "Sim", "Sim"]))  # data quebrada
    c.update(linha(12, "B", ["26/02/2026", "masc", "Não", "Não", "Não"]))
    # linha 12 em branco no meio do bloco de jogos, depois mais um jogo
    c.update(linha(13, "L", ["29/03/2026", "Masc Amistoso", "Sim", "Sim", "Amistoso "]))
    # Bloco de março colado no de fevereiro, sem linha em branco
    c.update({"B13": "Março"})
    c.update(linha(14, "B", ["Data", "Equipe", "Confirmado", "Técnico", "Quadra"]))
    c.update(linha(15, "B", ["02/03/2026", "Fem Atcup", "Sim", "Sim", "Sim"]))
    c.update(linha(16, "B", ["02/03/2026", "Fem", "Sim", "Sim", "Sim"]))  # repetido
    c.update(linha(17, "B", ["", "Torcida", "Sim", "", ""]))  # sem data
    return grade(c)


def aba_handebol():
    """Handebol: quadra com valor por naipe."""
    c = {"B2": "Custos dos treinos"}
    c.update(linha(3, "B", ["Custo", "Descrição", "Valor"]))
    c.update(linha(4, "B", ["Técnico", "Vitinho", "100"]))
    c.update(linha(5, "B", ["Quadra masc", "Minho ", "200"]))
    c.update(linha(6, "B", ["Quadra fem", "Minho", "180"]))
    c.update({"B8": "Agosto"})
    c.update(linha(9, "B", ["Data", "Equipe", "Confirmado", "Técnico", "Quadra"]))
    c.update(linha(10, "B", ["10/08/2026", "Fem", "Sim", "Sim", "Sim"]))
    c.update(linha(11, "B", ["11/08/2026", "Masc", "Sim", "Sim", "Sim"]))
    return grade(c)


def treinos():
    return {"FUTSAL": aba_futsal(), "HANDEBOL": aba_handebol()}
