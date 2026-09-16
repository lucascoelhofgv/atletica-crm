"""Importa uma FESTA a partir das planilhas modelo Jungle / FRAT HOUSE.

Essas planilhas não são tabelas: são blocos soltos. Este parser procura, no
TOPO da aba (ano corrente), três blocos:

* Lotes de ingresso  — cabeçalho "Lotes oficiais" / "Previsão Lotes" / "Vendas Lotes"
* Custos Fixos        — cabeçalho "Custos Fixos"
* Custos Variáveis    — cabeçalho "Custos Variáveis"

De cada linha ele tira nome/item, quantidade e valor unitário, sempre relativo
à posição da primeira célula preenchida (as planilhas têm colunas vazias à
esquerda). O resultado é mostrado em PRÉVIA antes de gravar.
"""

from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def _num(s: str):
    """'1.020' -> 1020 ; '12' -> 12 ; '425,53' -> 425.53 ; 'X'/'' -> None."""
    s = (s or "").strip()
    if not s or _norm(s) in {"x", "-", "#ref!", "n/a"}:
        return None
    s = s.replace(".", "").replace(",", ".")
    s = re.sub(r"[^0-9.\-]", "", s)
    if not s or s in {".", "-"}:
        return None
    try:
        v = float(s)
        return int(v) if v == int(v) else round(v, 2)
    except ValueError:
        return None


def _money(s: str):
    """'R$4.500,00' / '$1,90' / '-R$12.594,77' -> Decimal ; lixo -> None."""
    s = (s or "").strip()
    if not s or _norm(s) in {"x", "-", "#ref!"}:
        return None
    neg = s.lstrip().startswith("-") or "-r$" in _norm(s)
    limpo = re.sub(r"[^0-9.,]", "", s)
    if not limpo:
        return None
    if "," in limpo:                       # formato BR: 4.500,00
        limpo = limpo.replace(".", "").replace(",", ".")
    try:
        v = Decimal(limpo)
        return -v if neg else v
    except InvalidOperation:
        return None


CAB_LOTE = {"lotes oficiais", "previsao lotes", "vendas lotes", "lotes"}
PARAR = {"total", "soma", "total com porta", "breakeven", "", "por pessoa",
         "custos fixos", "custos variaveis", "custos", "item"}


def _cel(linha, k):
    return linha[k].strip() if 0 <= k < len(linha) and linha[k] else ""


def _achar_bloco(grid, chaves):
    """(linha, coluna) da 1ª célula cujo texto normalizado está em `chaves`."""
    for r, linha in enumerate(grid):
        for c, cel in enumerate(linha):
            if _norm(cel) in chaves:
                return r, c
    return None, None


def _fim_coluna(grid, r0, c0, altura=18):
    """Primeira coluna, à direita de c0, totalmente vazia no bloco -> limite."""
    largura = max(len(l) for l in grid[r0:r0 + altura]) if grid[r0:r0 + altura] else c0
    for k in range(c0 + 1, largura + 1):
        if all(not _cel(l, k) for l in grid[r0:r0 + altura]):
            return k
    return largura + 1


def _dividir(fatia):
    """(nome, [dinheiros], [numeros]) de uma fatia de linha (só o bloco)."""
    uteis = [c.strip() for c in fatia if c and c.strip()]
    if not uteis:
        return "", [], []
    nome = uteis[0]
    resto = uteis[1:]
    dinheiros = [d for d in (_money(c) for c in resto if "$" in c) if d is not None]
    numeros = [n for n in (_num(c) for c in resto if "$" not in c) if n is not None]
    return nome, dinheiros, numeros


def _ler_lotes(grid):
    r, c = _achar_bloco(grid, CAB_LOTE)
    if r is None:
        return []
    c_fim = _fim_coluna(grid, r, c)
    itens = []
    for linha in grid[r + 1:r + 40]:
        nome, dinheiros, numeros = _dividir(linha[c:c_fim])
        if _norm(nome) in PARAR or _norm(nome).startswith("custos"):
            break
        if not nome or (not numeros and not dinheiros):
            continue
        qtd = numeros[0] if numeros else 0
        val = dinheiros[0] if dinheiros else Decimal("0")
        itens.append({"nome": nome, "quantidade": int(qtd) if qtd else 0,
                      "valor_unitario": val})
    return itens


def _ler_custos(grid, chave, tipo):
    r, c = _achar_bloco(grid, {chave})
    if r is None:
        return []
    c_fim = _fim_coluna(grid, r, c)
    inicio = r + 1
    if _norm(_cel(grid[inicio], c)) in {"item", "descricao", "quantidade"}:
        inicio += 1
    itens = []
    for linha in grid[inicio:inicio + 60]:
        nome, dinheiros, numeros = _dividir(linha[c:c_fim])
        n = _norm(nome)
        if n in PARAR or n.startswith("por pessoa") or n.startswith("custos"):
            break
        if not nome or not dinheiros:
            continue
        val = dinheiros[-2] if len(dinheiros) >= 2 else dinheiros[0]
        qtd = numeros[-1] if numeros else 1
        itens.append({"tipo": tipo, "item": nome,
                      "quantidade": qtd or 1, "valor_unitario": val})
    return itens


def analisar(grid):
    """Devolve {'lotes': [...], 'custos': [...]} para a prévia."""
    return {
        "lotes": _ler_lotes(grid),
        "custos": (_ler_custos(grid, "custos fixos", "fixo")
                   + _ler_custos(grid, "custos variaveis", "variavel")),
    }


def criar_festa(dados, nome, data, local="", capacidade=None, staff=0,
                usuario=None):
    """Cria o Evento (festa) + lotes + custos a partir do dict de `analisar`."""
    from .models import CustoEvento, Evento, LoteIngresso

    ev = Evento.objects.create(
        nome=nome, tipo=Evento.Tipo.FESTA, status=Evento.Status.REALIZADO,
        data=data, local=local, capacidade=capacidade, staff_cortesias=staff or 0,
        observacoes="Importado de planilha.",
        criado_por=usuario if getattr(usuario, "pk", None) else None,
    )
    for ordem, l in enumerate(dados.get("lotes", [])):
        LoteIngresso.objects.create(
            evento=ev, nome=l["nome"][:80], ordem=ordem,
            quantidade_prevista=l["quantidade"] or 0,
            quantidade_vendida=l["quantidade"] or 0,
            valor_unitario=l["valor_unitario"],
        )
    for c in dados.get("custos", []):
        CustoEvento.objects.create(
            evento=ev, tipo=c["tipo"], item=c["item"][:160],
            quantidade=c["quantidade"] or 1, valor_unitario=c["valor_unitario"],
        )
    return ev
