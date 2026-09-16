"""Google Sheets (exportação) e importação de planilhas, para a tela antiga
e a API. As chamadas ao gspread levam segundos; quem chama trata timeout."""

from django.conf import settings

from ..models import registrar_atividade
from ..sheets import SheetsIndisponivel, exportar_tudo, ler_aba

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


__all__ = ["SheetsIndisponivel", "situacao", "exportar_sheets", "exportar_festas",
           "previa_importacao", "importar"]
