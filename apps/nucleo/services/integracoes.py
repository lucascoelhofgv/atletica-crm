"""Google Sheets (exportação) e importação de planilhas, para a tela antiga
e a API. As chamadas ao gspread levam segundos; quem chama trata timeout."""

from django.conf import settings

from ..models import registrar_atividade
from ..sheets import SheetsIndisponivel, exportar_tudo, ler_aba, ler_abas, ler_grade

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


def email_conta_servico() -> str:
    """E-mail com quem a diretoria precisa compartilhar a planilha. Vazio se
    a credencial não estiver configurada."""
    from ..sheets import _credenciais

    try:
        return _credenciais().service_account_email
    except Exception:
        return ""


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


# --------------------------------------------------------------------------- #
# Fontes de planilha: o que o comando agendado e o botão "Sincronizar" rodam
# --------------------------------------------------------------------------- #
def _avisos(resumo, detalhes):
    avisos = detalhes.get("avisos") or []
    if avisos:
        resumo += f", {len(avisos)} aviso(s)"
    return resumo


def executar_fonte(fonte, simular=False, usuario=None) -> dict:
    """Roda o importador do destino da fonte. Devolve ``{"resumo": linha
    legível, "avisos": [...]}``; com ``simular`` só lê, não grava."""
    from ..models import FontePlanilha

    Destino = FontePlanilha.Destino

    if fonte.destino == Destino.ESPORTES_ORCAMENTO:
        from apps.esportes import services as esportes

        grade = ler_grade(fonte.planilha, fonte.aba or None)
        if simular:
            p = esportes.previa_orcamento(grade)
            return {"resumo": _avisos(
                f"{p['modalidades']} modalidade(s), semestres {', '.join(p['semestres']) or 'nenhum'}", p),
                "avisos": p["avisos"]}
        r = esportes.importar_orcamento(grade, usuario=usuario)
        return {"resumo": _avisos(
            f"{r['modalidades']} modalidade(s): {r['criados']} orçamento(s) novo(s), "
            f"{r['atualizados']} atualizado(s), {r['removidos']} removido(s)", r),
            "avisos": r["avisos"]}

    if fonte.destino == Destino.ESPORTES_TREINOS:
        from apps.esportes import services as esportes

        grades = ler_abas(fonte.planilha)
        if fonte.aba:
            grades = {k: v for k, v in grades.items() if k.strip().lower() == fonte.aba.strip().lower()}
        if simular:
            p = esportes.previa_treinos(grades)
            return {"resumo": _avisos(f"{p['treinos']} treino(s) e {p['jogos']} jogo(s)", p),
                    "avisos": p["avisos"]}
        r = esportes.importar_treinos(grades, usuario=usuario)
        return {"resumo": _avisos(
            f"{r['criados']} novo(s), {r['atualizados']} atualizado(s), {r['removidos']} removido(s)", r),
            "avisos": r["avisos"]}

    if fonte.destino == Destino.CONTROLE_PRODUTOS:
        if simular:
            p = previa_controle_produtos(fonte.planilha)
            return {"resumo": (
                f"{p['produtos']} produto(s), {p['compras_recebidas']} de "
                f"{p['compras_total']} compra(s) recebida(s), {p['vendas']} venda(s)"
            ), "avisos": []}
        r = importar_controle_produtos(fonte.planilha, usuario=usuario)
        avisos = [f"{aba}: {erro}" for aba, dados in r.items() for erro in dados.get("erros", [])]
        return {"resumo": _avisos(", ".join(
            f"{aba} {dados['criados']} novo(s)" for aba, dados in r.items()
        ), {"avisos": avisos}), "avisos": avisos}

    if simular:
        p = previa_importacao(fonte.planilha, fonte.aba, fonte.destino)
        return {"resumo": f"{p['total_linhas']} linha(s) em {len(p['cabecalho'])} coluna(s)",
                "avisos": []}

    r = importar(fonte.planilha, fonte.aba, fonte.destino, fonte.modo, usuario=usuario)
    resumo = (
        f"{r['criados']} criado(s), {r['atualizados']} atualizado(s), "
        f"{r['ignorados']} ignorado(s)"
    )
    if r.get("erros"):
        resumo += f", {len(r['erros'])} erro(s)"
    return {"resumo": resumo, "avisos": r.get("erros", [])}


def sincronizar_fonte(fonte, usuario=None, simular=False) -> dict:
    """Executa a fonte e guarda nela o resultado ou o erro. Relança o erro
    depois de guardar, para quem chamou decidir como mostrar."""
    from django.utils import timezone

    try:
        resultado = executar_fonte(fonte, simular=simular, usuario=usuario)
    except Exception as exc:
        if not simular:
            fonte.ultimo_erro = str(exc)[:255]
            fonte.save(update_fields=["ultimo_erro"])
        raise

    if not simular:
        fonte.ultima_sincronizacao = timezone.now()
        fonte.ultimo_resultado = resultado["resumo"][:255]
        fonte.ultimo_erro = ""
        fonte.save(update_fields=["ultima_sincronizacao", "ultimo_resultado", "ultimo_erro"])
    return resultado


__all__ = ["SheetsIndisponivel", "situacao", "exportar_sheets", "exportar_festas",
           "previa_importacao", "importar", "previa_festa", "importar_festa",
           "previa_controle_produtos", "importar_controle_produtos",
           "executar_fonte", "sincronizar_fonte"]
