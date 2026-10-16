"""Leitura das planilhas de Esportes (Orçamento e Treinos).

Funções puras: recebem a grade de texto que ``apps.nucleo.sheets`` devolve
(lista de linhas, cada uma lista de strings) e devolvem dicionários prontos
para gravar, mais uma lista de avisos legíveis. Nada aqui toca no banco, o
que deixa a prévia e os testes simples.

As duas planilhas são feitas à mão e têm ruído: "Masc ", "masc", "Fem Atcup",
blocos de mês com o título errado, linha sem data. A regra é ler o que dá,
nunca quebrar a importação inteira por uma linha, e contar o que ficou de fora.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, time
from decimal import Decimal, InvalidOperation

MESES = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]

#: Apelidos que aparecem nas planilhas -> nome do esporte no CRM.
ESPORTES = {
    "hand": "Handebol", "handebol": "Handebol", "handball": "Handebol",
    "volei": "Vôlei", "voleibol": "Vôlei", "vol": "Vôlei",
    "basquete": "Basquete", "basq": "Basquete", "basketball": "Basquete",
    "futsal": "Futsal", "fut": "Futsal",
    "bateria": "Bateria",
}

NAIPES = {
    "masc": "masc", "masculino": "masc", "m": "masc",
    "fem": "fem", "feminino": "fem", "f": "fem",
}


def _norm(s) -> str:
    s = str(s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s)


def _cel(grade, r, c) -> str:
    if r < 0 or r >= len(grade) or c < 0 or c >= len(grade[r]):
        return ""
    return (grade[r][c] or "").strip()


def _coord(r, c) -> str:
    """Endereço no estilo da planilha (linha e coluna contadas a partir de 0)."""
    letras = ""
    c += 1
    while c:
        c, resto = divmod(c - 1, 26)
        letras = chr(65 + resto) + letras
    return f"{letras}{r + 1}"


def _dinheiro(s) -> Decimal | None:
    """'86,5', '1.300,00', 'R$ 200' ou '86.5'. O último separador com uma ou
    duas casas depois dele é o decimal."""
    limpo = re.sub(r"[^0-9.,\-]", "", str(s or ""))
    if not limpo or limpo == "-":
        return None
    pos = max(limpo.rfind("."), limpo.rfind(","))
    if pos != -1 and len(limpo) - pos - 1 in (1, 2):
        inteiro = re.sub(r"[.,]", "", limpo[:pos])
        limpo = f"{inteiro or '0'}.{limpo[pos + 1:]}"
    else:
        limpo = re.sub(r"[.,]", "", limpo)
    try:
        return Decimal(limpo)
    except InvalidOperation:
        return None


def _inteiro(s) -> int | None:
    v = _dinheiro(s)
    return int(v) if v is not None else None


def _data(s):
    s = str(s or "").strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s.split(" ")[0], fmt).date()
        except ValueError:
            continue
    return None


def _hora(s) -> time | None:
    m = re.match(r"^(\d{1,2})[:h](\d{2})", str(s or "").strip())
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    return time(h, mi) if h < 24 and mi < 60 else None


def _sim(s) -> bool:
    return _norm(s) in {"sim", "s", "x", "true", "ok", "pago"}


def _juntar(*partes) -> str:
    """Junta textos sem repetir o mesmo ('Amistoso' na equipe e na coluna ao lado)."""
    vistos, saida = set(), []
    for p in partes:
        if p and _norm(p) not in vistos:
            vistos.add(_norm(p))
            saida.append(p.strip())
    return " ".join(saida)


def esporte_canonico(texto: str) -> str:
    chave = _norm(texto)
    if chave in ESPORTES:
        return ESPORTES[chave]
    return str(texto or "").strip().title()


def separar_modalidade(texto: str) -> tuple[str, str]:
    """'Hand Feminino' -> ('Handebol', 'fem'); 'Bateria' -> ('Bateria', 'misto')."""
    partes = str(texto or "").split()
    if len(partes) > 1 and _norm(partes[-1]) in NAIPES:
        return esporte_canonico(" ".join(partes[:-1])), NAIPES[_norm(partes[-1])]
    return esporte_canonico(texto), "misto"


def separar_equipe(texto: str) -> tuple[str | None, str]:
    """'Masc Amistoso' -> ('masc', 'Amistoso'); 'Fem ' -> ('fem', '')."""
    partes = str(texto or "").split()
    if not partes:
        return None, ""
    naipe = NAIPES.get(_norm(partes[0]))
    if naipe is None:
        return None, str(texto).strip()
    return naipe, " ".join(partes[1:]).strip()


# --------------------------------------------------------------------------- #
# Orçamento
# --------------------------------------------------------------------------- #
def analisar_orcamento(grade) -> dict:
    """Lê a tabela de modalidades (a que tem 'Modalidade' no cabeçalho).

    O resto da aba (rascunhos, listas de atletas) é ignorado de propósito.
    """
    avisos: list[str] = []
    cab = None
    for r, linha in enumerate(grade):
        for c, valor in enumerate(linha):
            if _norm(valor) == "modalidade":
                cab = (r, c)
                break
        if cab:
            break
    if not cab:
        return {"modalidades": [], "avisos": [
            "Não achei a tabela de orçamento: falta uma célula escrita 'Modalidade' no cabeçalho."
        ]}

    r0, c0 = cab
    colunas = {}
    for c in range(c0, len(grade[r0])):
        nome = _norm(grade[r0][c])
        if not nome:
            continue
        if nome == "modalidade":
            colunas["modalidade"] = c
        elif nome == "dia":
            colunas["dia"] = c
        elif nome == "inicio":
            colunas["inicio"] = c
        elif nome in ("termino", "fim"):
            colunas["fim"] = c
        elif nome == "local":
            colunas["local"] = c
        elif nome.startswith("custo aluguel") or nome.startswith("custo quadra"):
            colunas["quadra"] = c
        elif nome.startswith("custo treinador") and "jogo" in nome:
            colunas["treinador_jogo"] = c
        elif nome.startswith("custo treinador"):
            colunas["treinador_treino"] = c
        else:
            m = re.match(r"qtd (treinos|jogos) (\d{4})\.(\d)", nome)
            if m:
                colunas[(m.group(1), int(m.group(2)), int(m.group(3)))] = c

    semestres = sorted({(k[1], k[2]) for k in colunas if isinstance(k, tuple)})
    if not semestres:
        avisos.append("O cabeçalho não tem colunas 'QTD Treinos AAAA.S'; nenhum semestre lido.")

    modalidades = []
    for r in range(r0 + 1, len(grade)):
        nome = _cel(grade, r, colunas["modalidade"])
        if not nome:
            # Linha de total ou fim da tabela.
            if not any(_cel(grade, r, c) for c in colunas.values()):
                break
            continue
        esporte, naipe = separar_modalidade(nome)

        def valor(chave, conv=_dinheiro):
            c = colunas.get(chave)
            return conv(_cel(grade, r, c)) if c is not None else None

        item = {
            "linha": r + 1,
            "nome_planilha": nome,
            "esporte": esporte,
            "naipe": naipe,
            "dia_semana": _cel(grade, r, colunas["dia"]) if "dia" in colunas else "",
            "horario_inicio": valor("inicio", _hora),
            "horario_fim": valor("fim", _hora),
            "local": _cel(grade, r, colunas["local"]) if "local" in colunas else "",
            "custo_quadra_hora": valor("quadra") or Decimal("0"),
            "custo_treinador_treino": valor("treinador_treino") or Decimal("0"),
            "custo_treinador_jogo": valor("treinador_jogo") or Decimal("0"),
            "semestres": [],
        }
        for ano, sem in semestres:
            treinos = valor(("treinos", ano, sem), _inteiro)
            jogos = valor(("jogos", ano, sem), _inteiro)
            if treinos is None and jogos is None:
                continue
            item["semestres"].append({
                "ano": ano, "semestre": sem,
                "treinos_previstos": max(treinos or 0, 0),
                "jogos_previstos": max(jogos or 0, 0),
            })
        modalidades.append(item)

    vistos = set()
    for m in modalidades:
        chave = (m["esporte"], m["naipe"])
        if chave in vistos:
            avisos.append(f"Linha {m['linha']}: '{m['nome_planilha']}' aparece duas vezes; ficou a primeira.")
        vistos.add(chave)
    modalidades = [m for i, m in enumerate(modalidades)
                   if (m["esporte"], m["naipe"]) not in
                   {(o["esporte"], o["naipe"]) for o in modalidades[:i]}]

    return {"modalidades": modalidades, "avisos": avisos}


# --------------------------------------------------------------------------- #
# Treinos
# --------------------------------------------------------------------------- #
def _ler_tabela_custos(grade, r, c) -> dict:
    """Bloco 'Custos dos treinos' / 'Custos dos jogos': linhas Custo | Descrição
    | Valor logo abaixo do título. Devolve {'tecnico', 'quadra', 'quadra_masc',
    'quadra_fem'} com o que encontrar."""
    custos = {}
    for rr in range(r + 1, min(r + 8, len(grade))):
        rotulo = _norm(_cel(grade, rr, c))
        if not rotulo:
            if custos:
                break
            continue
        if rotulo == "custo":
            continue
        valor = _dinheiro(_cel(grade, rr, c + 2))
        if valor is None:
            continue
        if rotulo.startswith("tecnico") or rotulo.startswith("treinador"):
            custos.setdefault("tecnico", valor)
        elif rotulo.startswith("quadra"):
            resto = rotulo.replace("quadra", "").strip()
            naipe = NAIPES.get(resto)
            custos["quadra_" + naipe if naipe else "quadra"] = valor
    return custos


def _eh_titulo_de_bloco(texto) -> bool:
    n = _norm(texto)
    return n == "data" or n in MESES


def analisar_aba_treinos(nome_aba: str, grade) -> dict:
    esporte = esporte_canonico(nome_aba)
    avisos: list[str] = []
    custos_treino, custos_jogo = {}, {}
    col_jogos = None

    for r, linha in enumerate(grade):
        for c, valor in enumerate(linha):
            n = _norm(valor)
            if n == "custos dos treinos":
                custos_treino = _ler_tabela_custos(grade, r, c)
            elif n == "custos dos jogos":
                custos_jogo = _ler_tabela_custos(grade, r, c)
                col_jogos = c

    if "tecnico" not in custos_treino:
        avisos.append(f"{nome_aba}: não achei o valor do técnico em 'Custos dos treinos'; contei R$ 0.")

    sessoes = []
    for r, linha in enumerate(grade):
        for c, valor in enumerate(linha):
            if _norm(valor) != "data" or _norm(_cel(grade, r, c + 1)) != "equipe":
                continue
            cab = {_norm(_cel(grade, r, cc)): cc for cc in range(c, c + 5) if _cel(grade, r, cc)}
            col_obs = [cc for cc in range(c + 1, c + 5) if not _cel(grade, r, cc)]
            tipo = "jogo" if (col_jogos is not None and c >= col_jogos) or "quadra" not in cab else "treino"

            for rr in range(r + 1, len(grade)):
                bruto_data = _cel(grade, rr, c)
                bruto_equipe = _cel(grade, rr, cab.get("equipe", c + 1))
                if _eh_titulo_de_bloco(bruto_data):
                    break  # começou o bloco do mês seguinte sem linha em branco
                if not bruto_data and not bruto_equipe:
                    # Uma linha em branco no meio do bloco acontece; só encerra
                    # se a de baixo também não começar com uma data.
                    if _data(_cel(grade, rr + 1, c)):
                        continue
                    break
                onde = f"{nome_aba} {_coord(rr, c)}"
                data = _data(bruto_data)
                if not data:
                    avisos.append(f"{onde}: linha sem data válida ('{bruto_data}'), ficou de fora.")
                    continue
                naipe, obs = separar_equipe(bruto_equipe)
                if naipe is None:
                    avisos.append(f"{onde}: equipe '{bruto_equipe}' não é Masc nem Fem, ficou de fora.")
                    continue
                extra = " ".join(_cel(grade, rr, cc) for cc in col_obs if _cel(grade, rr, cc))
                teve_tecnico = _sim(_cel(grade, rr, cab["tecnico"])) if "tecnico" in cab else False
                teve_quadra = _sim(_cel(grade, rr, cab["quadra"])) if "quadra" in cab else False

                if tipo == "jogo":
                    valor_tecnico = custos_jogo.get("tecnico", custos_treino.get("tecnico", Decimal("0")))
                    valor_quadra = Decimal("0")
                else:
                    valor_tecnico = custos_treino.get("tecnico", Decimal("0"))
                    valor_quadra = custos_treino.get(
                        f"quadra_{naipe}", custos_treino.get("quadra", Decimal("0"))
                    )

                sessoes.append({
                    "esporte": esporte,
                    "naipe": naipe,
                    "tipo": tipo,
                    "data": data,
                    "confirmada": _sim(_cel(grade, rr, cab["confirmado"])) if "confirmado" in cab else True,
                    "teve_tecnico": teve_tecnico,
                    "teve_quadra": teve_quadra,
                    "custo_tecnico": valor_tecnico,
                    "custo_quadra": valor_quadra,
                    "custo": (valor_tecnico if teve_tecnico else 0) + (valor_quadra if teve_quadra else 0),
                    "observacao": _juntar(obs, extra)[:120],
                    "origem": onde,
                })

    return {
        "esporte": esporte,
        "custos_treino": custos_treino,
        "custos_jogo": custos_jogo,
        "sessoes": sessoes,
        "avisos": avisos,
    }


def analisar_treinos(grades: dict) -> dict:
    """Todas as abas da planilha de Treinos. Uma sessão por (modalidade, tipo,
    dia): se a mesma aparece duas vezes, fica a primeira e sai um aviso."""
    sessoes, avisos, esportes = [], [], []
    vistas = {}
    for nome_aba, grade in grades.items():
        aba = analisar_aba_treinos(nome_aba, grade)
        if not aba["sessoes"]:
            avisos.append(f"{nome_aba}: nenhuma linha de treino ou jogo encontrada.")
            avisos.extend(aba["avisos"])
            continue
        esportes.append(aba["esporte"])
        avisos.extend(aba["avisos"])
        for s in aba["sessoes"]:
            chave = (s["esporte"], s["naipe"], s["tipo"], s["data"])
            if chave in vistas:
                avisos.append(
                    f"{s['origem']}: {s['tipo']} de {s['data']:%d/%m/%Y} repetido "
                    f"(já estava em {vistas[chave]}), ficou o primeiro."
                )
                continue
            vistas[chave] = s["origem"]
            sessoes.append(s)
    return {"esportes": esportes, "sessoes": sessoes, "avisos": avisos}
