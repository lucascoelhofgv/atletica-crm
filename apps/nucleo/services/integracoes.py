"""Google Sheets (exportação) e importação de planilhas, para a tela antiga
e a API. As chamadas ao gspread levam segundos; quem chama trata timeout."""

from django.conf import settings

from ..models import registrar_atividade
from ..sheets import SheetsIndisponivel, exportar_tudo, ler_aba, ler_grade

PLANILHAS_SUGERIDAS = [
    {"rotulo": "Relação com Empresas (→ Fornecedores)",
     "planilha": "1D4sv6PVM3pjGCanbKLxaOrXsgS4lF3vgDej8ORwmfLg", "destino": "fornecedores"},
    {"rotulo": "Relação Padrinhos e Membros (→ Clientes)",
     "planilha": "1z7SJNAzgGruUZMSU5xBrmzhb87BdPleHHlHsDcBvC38", "destino": "clientes"},
]


def situacao() -> dict:
    from ..importadores import IMPORTADORES

    planilha = getattr(settings, "GOOGLE_SHEETS_SPREADSHEET_ID", "")
    return {
        "configurado": bool(planilha),
        "planilha_id": planilha,
        "url_planilha": f"https://docs.google.com/spreadsheets/d/{planilha}/edit" if planilha else "",
        "abas_exportadas": ["Clientes", "Produtos", "Pedidos", "Festas"],
        "destinos": [{"valor": k, "rotulo": v[0]} for k, v in IMPORTADORES.items()],
        "sugeridas": PLANILHAS_SUGERIDAS,
    }


def exportar_sheets(usuario) -> dict:
    resumo = exportar_tudo()
    registrar_atividade(usuario, "sincronizou Google Sheets",
                        ", ".join(f"{k}: {v}" for k, v in resumo.items()))
    return resumo


def exportar_festas(usuario) -> int:
    from apps.eventos.sheets import exportar_festas as _exportar

    n = _exportar()
    registrar_atividade(usuario, "sincronizou festas com Sheets", f"{n} evento(s)")
    return n


def previa_importacao(planilha: str, aba: str | None, destino: str, amostra: int = 8) -> dict:
    from ..importadores import IMPORTADORES

    if destino not in IMPORTADORES:
        raise ValueError("Destino inválido.")
    linhas, cabecalho = ler_aba(planilha, aba or None)
    return {
        "destino": destino,
        "destino_rotulo": IMPORTADORES[destino][0],
        "cabecalho": cabecalho,
        "amostra": [[registro.get(c, "") for c in cabecalho] for registro in linhas[:amostra]],
        "total_linhas": len(linhas),
    }


def importar(planilha: str, aba: str | None, destino: str, modo: str, usuario) -> dict:
    from ..importadores import IMPORTADORES

    if destino not in IMPORTADORES:
        raise ValueError("Destino inválido.")
    rotulo, funcao = IMPORTADORES[destino]
    linhas, _ = ler_aba(planilha, aba or None)
    origem = f"planilha ({aba or 'aba 1'})"
    resumo = funcao(linhas, origem=origem, modo=modo, usuario=usuario)
    registrar_atividade(usuario, f"importou {rotulo} de planilha",
                        f"{resumo['criados']} criados, {resumo['atualizados']} atualizados")
    return {"destino_rotulo": rotulo, **resumo, "erros": resumo.get("erros", [])[:50]}


# --------------------------------------------------------------------------- #
# Festa (Jungle / FRAT HOUSE) — planilha em blocos, não em tabela simples
# --------------------------------------------------------------------------- #
def previa_festa(planilha: str, aba: str | None, linha_inicial: int | None) -> dict:
    from apps.eventos.importador_festa import analisar

    grade = ler_grade(planilha, aba or None)
    if linha_inicial:
        grade = grade[linha_inicial - 1:]
    dados = analisar(grade)
    receita = sum(l["quantidade"] * l["valor_unitario"] for l in dados["lotes"])
    custo = sum(c["quantidade"] * c["valor_unitario"] for c in dados["custos"])
    return {
        "lotes": dados["lotes"],
        "custos": dados["custos"],
        "total_ingressos": sum(l["quantidade"] for l in dados["lotes"]),
        "receita_ingressos": receita,
        "custo_total": custo,
        "resultado": receita - custo,
    }


def importar_festa(planilha: str, aba: str | None, linha_inicial: int | None,
                   nome: str, data, local: str, capacidade, staff, usuario) -> dict:
    from apps.eventos.importador_festa import analisar, criar_festa

    grade = ler_grade(planilha, aba or None)
    if linha_inicial:
        grade = grade[linha_inicial - 1:]
    dados = analisar(grade)
    if not dados["lotes"] and not dados["custos"]:
        raise ValueError(
            "Não encontrei blocos de Lotes/Custos no topo dessa aba. Confira "
            "o nome da aba ou informe a linha inicial."
        )
    ev = criar_festa(dados, nome=nome, data=data, local=local or "",
                     capacidade=capacidade, staff=staff or 0, usuario=usuario)
    registrar_atividade(usuario, "importou festa de planilha", ev.nome)
    return {
        "evento_id": ev.pk, "nome": ev.nome,
        "lotes": ev.lotes.count(), "custos": ev.custos.count(),
        "resultado": ev.resultado, "margem": ev.margem,
    }


# --------------------------------------------------------------------------- #
# Controle de Produtos (planilha real: cadastro + compras + vendas)
# --------------------------------------------------------------------------- #
ABAS_CONTROLE_PRODUTOS = {"produtos": "Produtos", "pedidos": "Pedidos", "vendas": "Vendas"}


def _grades_controle_produtos(planilha: str) -> dict:
    return {
        chave: ler_grade(planilha, aba)
        for chave, aba in ABAS_CONTROLE_PRODUTOS.items()
    }


def previa_controle_produtos(planilha: str) -> dict:
    from apps.catalogo.importador_planilha import analisar

    g = _grades_controle_produtos(planilha)
    return analisar(g["produtos"], g["pedidos"], g["vendas"])


def importar_controle_produtos(planilha: str, usuario) -> dict:
    from apps.catalogo.importador_planilha import importar_tudo

    g = _grades_controle_produtos(planilha)
    resumo = importar_tudo(g["produtos"], g["pedidos"], g["vendas"], usuario=usuario)
    registrar_atividade(
        usuario, "importou Controle de Produtos de planilha",
        ", ".join(f"{k}: {v['criados']}" for k, v in resumo.items()),
    )
    return resumo


__all__ = ["SheetsIndisponivel", "situacao", "exportar_sheets", "exportar_festas",
           "previa_importacao", "importar", "previa_festa", "importar_festa",
           "previa_controle_produtos", "importar_controle_produtos"]
