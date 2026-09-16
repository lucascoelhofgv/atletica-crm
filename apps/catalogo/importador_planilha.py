"""Importa a planilha real "Controle de Produtos" da Atlética (cadastro,
compras/recebimentos e vendas de balcão/estande).

Abas esperadas (nomes exatos na planilha, uma vez convertida para Google
Sheets — a conversão preserva as abas do Excel original):

* **Produtos** — cadastro: ID, Categoria, Produto, Fornecedor, Custo
  Unitário, Preço de Venda, Estoque Mínimo, Estoque Atual, Status.
* **Pedidos**  — compras/entradas de estoque: ID, Mês, Descrição, Produto,
  Quantidade, Custo Unitário, Subtotal, Frete, Custo Total, Status,
  Observações. Só as linhas com Status "Recebido" viram movimentação de
  estoque — "Planejado" fica de fora até ser recebido de verdade.
* **Vendas**   — registro por evento: ID, Mês, Data, Evento, Produto,
  Quantidade Vendida, Preço Unit., Receita, Custo Unit., CMV, Margem.
  Não tem cliente identificado -> vira pedido do cliente **"Venda Stand"**
  (dá pra trocar depois, normalmente, editando o cliente do pedido).

O saldo de estoque de cada produto NÃO é copiado da coluna "Estoque Atual" —
ele nasce do histórico de movimentações (compras recebidas menos vendas),
igual a planilha faz na aba "Estoque". Assim o saldo fica auditável.

Idempotente: cada linha da planilha (PD01, VD03...) é marcada no registro
criado; rodar de novo não duplica.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation

MARCADOR = "planilha-controle-produtos"


def _norm(s) -> str:
    s = str(s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def _num(s):
    s = str(s or "").strip()
    if not s or _norm(s) in {"x", "-", "n/a"}:
        return None
    s = s.replace(".", "").replace(",", ".")
    s = re.sub(r"[^0-9.\-]", "", s)
    try:
        v = float(s)
        return int(v) if v == int(v) else v
    except ValueError:
        return None


def _dinheiro(s):
    """Aceita tanto 'R$ 16.78' (ponto decimal) quanto 'R$1.020,00' (vírgula
    decimal) — detecta pelo ÚLTIMO separador da string."""
    s = str(s or "").strip()
    if not s or _norm(s) in {"x", "-", "n/a"}:
        return None
    neg = s.lstrip().startswith("-")
    limpo = re.sub(r"[^0-9.,]", "", s)
    if not limpo:
        return None
    pos = max(limpo.rfind("."), limpo.rfind(","))
    if pos == -1:
        inteiro, frac = limpo, "00"
    else:
        inteiro = re.sub(r"[.,]", "", limpo[:pos])
        frac = limpo[pos + 1:]
        if len(frac) not in (1, 2):  # era separador de milhar, não decimal
            inteiro, frac = inteiro + frac, "00"
    if not inteiro:
        inteiro = "0"
    try:
        v = Decimal(f"{inteiro}.{frac or '00'}")
        return -v if neg else v
    except InvalidOperation:
        return None


def _data(s):
    s = str(s or "").strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _achar_cabecalho(grid, precisa):
    """Linha cujas células (normalizadas) contêm todos os termos de `precisa`."""
    for i, linha in enumerate(grid):
        normed = [_norm(c) for c in linha]
        if all(any(p in n for n in normed) for p in precisa):
            return i
    return None


def _linhas_da_tabela(grid, precisa):
    """(cabecalho_norm->indice, linhas_de_dados) a partir do bloco encontrado."""
    i = _achar_cabecalho(grid, precisa)
    if i is None:
        return {}, []
    cabecalho = [_norm(c) for c in grid[i]]
    col = {}
    for idx, nome in enumerate(cabecalho):
        if nome and nome not in col:
            col[nome] = idx
    return col, grid[i + 1:]


def _cel(linha, col, *chaves, padrao=""):
    for chave in chaves:
        for nome, idx in col.items():
            if chave in nome and idx < len(linha):
                v = (linha[idx] or "").strip()
                if v:
                    return v
    return padrao


def _resumo():
    return {"criados": 0, "atualizados": 0, "ignorados": 0, "erros": []}


# --------------------------------------------------------------------------- #
def analisar(grid_produtos, grid_pedidos, grid_vendas):
    """Prévia (não grava nada): conta o que seria processado em cada aba."""
    col_p, linhas_p = _linhas_da_tabela(grid_produtos, ["id", "produto"])
    produtos = [l for l in linhas_p if _cel(l, col_p, "produto")]

    col_c, linhas_c = _linhas_da_tabela(grid_pedidos, ["id", "produto", "status"])
    compras = [l for l in linhas_c if _cel(l, col_c, "produto")]
    recebidas = [l for l in compras if "receb" in _norm(_cel(l, col_c, "status"))]

    col_v, linhas_v = _linhas_da_tabela(grid_vendas, ["id", "produto", "quantidade vendida"])
    vendas = [l for l in linhas_v
              if _cel(l, col_v, "produto") and _dinheiro(_cel(l, col_v, "preco unit")) is not None]

    return {
        "produtos": len(produtos),
        "compras_total": len(compras),
        "compras_recebidas": len(recebidas),
        "vendas": len(vendas),
    }


def importar_produtos(grid, usuario=None):
    from .models import CategoriaProduto, Produto

    r = _resumo()
    col, linhas = _linhas_da_tabela(grid, ["id", "produto"])
    if not col:
        r["erros"].append("Não encontrei o cabeçalho da aba Produtos (colunas ID/Produto).")
        return r

    for linha in linhas:
        nome = _cel(linha, col, "produto")
        if not nome:
            continue
        cat_nome = _cel(linha, col, "categoria")
        categoria = None
        if cat_nome:
            categoria, _c = CategoriaProduto.objects.get_or_create(nome=cat_nome[:60])

        fornecedor_nome = _cel(linha, col, "fornecedor")
        fornecedor = None
        if fornecedor_nome and _norm(fornecedor_nome) not in {"a definir", ""}:
            from apps.fornecedores.models import Fornecedor

            fornecedor = Fornecedor.objects.filter(nome__iexact=fornecedor_nome).first()

        custo = _dinheiro(_cel(linha, col, "custo unitario")) or Decimal("0")
        preco = _dinheiro(_cel(linha, col, "preco de venda")) or Decimal("0")
        minimo = _num(_cel(linha, col, "estoque minimo")) or 0

        produto = Produto.objects.filter(nome__iexact=nome).first()
        if produto:
            mudou = False
            for campo, valor in [("categoria", categoria), ("fornecedor", fornecedor)]:
                if valor and not getattr(produto, campo):
                    setattr(produto, campo, valor)
                    mudou = True
            if custo and not produto.custo_unitario:
                produto.custo_unitario, mudou = custo, True
            if preco and not produto.preco_venda:
                produto.preco_venda, mudou = preco, True
            if minimo and not produto.estoque_minimo:
                produto.estoque_minimo, mudou = minimo, True
            if mudou:
                produto.save()
                r["atualizados"] += 1
            else:
                r["ignorados"] += 1
        else:
            Produto.objects.create(
                nome=nome, categoria=categoria, fornecedor=fornecedor,
                custo_unitario=custo, preco_venda=preco, estoque_minimo=minimo,
                observacoes=f"Importado da planilha Controle de Produtos.",
                criado_por=usuario if getattr(usuario, "pk", None) else None,
            )
            r["criados"] += 1
    return r


def importar_compras(grid, usuario=None):
    from .models import MovimentacaoEstoque, Produto

    r = _resumo()
    col, linhas = _linhas_da_tabela(grid, ["id", "produto", "status"])
    if not col:
        r["erros"].append("Não encontrei o cabeçalho da aba Pedidos (colunas ID/Produto/Status).")
        return r

    for linha in linhas:
        pid = _cel(linha, col, "id")
        nome_produto = _cel(linha, col, "produto")
        status = _cel(linha, col, "status")
        if not nome_produto or "receb" not in _norm(status):
            continue

        marca = f"{MARCADOR} · compra {pid}"
        if MovimentacaoEstoque.objects.filter(motivo__icontains=marca).exists():
            r["ignorados"] += 1
            continue

        produto = Produto.objects.filter(nome__iexact=nome_produto).first()
        if not produto:
            r["erros"].append(f"Compra {pid}: produto '{nome_produto}' não encontrado.")
            continue

        qtd = _num(_cel(linha, col, "quantidade"))
        if not qtd:
            r["ignorados"] += 1
            continue

        descricao = _cel(linha, col, "descricao")
        try:
            produto.aplicar_movimentacao(
                tipo=MovimentacaoEstoque.Tipo.ENTRADA, quantidade=int(qtd),
                usuario=usuario if getattr(usuario, "pk", None) else None,
                motivo=f"{marca} — {descricao}"[:160],
            )
            r["criados"] += 1
        except Exception as exc:  # pragma: no cover
            r["erros"].append(f"Compra {pid}: {exc}")
    return r


def importar_vendas(grid, usuario=None, cliente_generico="Venda Stand"):
    from apps.crm.models import Cliente
    from apps.vendas.models import ItemPedido, Pedido

    from .models import Produto

    r = _resumo()
    col, linhas = _linhas_da_tabela(grid, ["id", "produto", "quantidade vendida"])
    if not col:
        r["erros"].append("Não encontrei o cabeçalho da aba Vendas.")
        return r

    cliente_balcao, _c = Cliente.objects.get_or_create(
        nome=cliente_generico,
        defaults={
            "relacionamento": Cliente.Relacionamento.RECORRENTE,
            "observacoes": (
                "Cliente genérico para vendas sem comprador identificado "
                "(planilha de controle de produtos / vendas de estande). "
                "Troque para o cliente real quando souber quem comprou."
            ),
        },
    )

    for linha in linhas:
        vid = _cel(linha, col, "id")
        nome_produto = _cel(linha, col, "produto")
        preco_txt = _cel(linha, col, "preco unit")
        if not nome_produto or _dinheiro(preco_txt) is None:
            continue  # linha de exemplo/placeholder sem preço real

        marca = f"{MARCADOR} · venda {vid}"
        if Pedido.objects.filter(observacoes__icontains=marca).exists():
            r["ignorados"] += 1
            continue

        produto = Produto.objects.filter(nome__iexact=nome_produto).first()
        if not produto:
            r["erros"].append(f"Venda {vid}: produto '{nome_produto}' não encontrado.")
            continue

        qtd = _num(_cel(linha, col, "quantidade vendida")) or 0
        if not qtd:
            r["ignorados"] += 1
            continue
        preco = _dinheiro(preco_txt) or produto.preco_venda
        if preco and not produto.preco_venda:
            # a aba Produtos costuma vir sem "Preço de Venda"; a primeira
            # venda real do produto serve de referência inicial
            produto.preco_venda = preco
            produto.save(update_fields=["preco_venda"])
        data_venda = _data(_cel(linha, col, "data")) or None
        evento = _cel(linha, col, "evento")

        try:
            pedido = Pedido(
                cliente=cliente_balcao,
                status=Pedido.Status.ENTREGUE,
                status_pagamento=Pedido.StatusPagamento.QUITADO,
                data_compra=data_venda or Pedido._meta.get_field("data_compra").get_default(),
                observacoes=f"{marca} — {evento}"[:255],
                criado_por=usuario if getattr(usuario, "pk", None) else None,
            )
            pedido.save()
            ItemPedido.objects.create(
                pedido=pedido, produto=produto, quantidade=int(qtd), preco_unitario=preco,
            )
            pedido.recalcular_total()
            pedido.aplicar_efeito_estoque(usuario=usuario)
            r["criados"] += 1
        except Exception as exc:  # pragma: no cover
            r["erros"].append(f"Venda {vid}: {exc}")
    return r


def importar_tudo(grid_produtos, grid_pedidos, grid_vendas, usuario=None):
    """Roda as três etapas em ordem (produtos precisam existir antes das
    compras/vendas que os referenciam)."""
    return {
        "produtos": importar_produtos(grid_produtos, usuario),
        "compras": importar_compras(grid_pedidos, usuario),
        "vendas": importar_vendas(grid_vendas, usuario),
    }
