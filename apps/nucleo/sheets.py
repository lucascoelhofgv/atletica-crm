"""Integração com o Google Sheets.

Exporta (e mantém sincronizadas) abas com Clientes, Produtos e Pedidos numa
planilha do Google. Útil para a diretoria acompanhar dados sem entrar no
sistema e para backup rápido.

Pré-requisitos (ver docs/DEPLOY.md, seção Google Sheets):
1. Criar um projeto no Google Cloud e ativar a API do Google Sheets + Drive.
2. Criar uma *service account* e baixar o JSON de credenciais.
3. Compartilhar a planilha de destino com o e-mail da service account (editor).
4. Definir no .env:
     GOOGLE_SERVICE_ACCOUNT_FILE=/caminho/para/credenciais.json
     GOOGLE_SHEETS_SPREADSHEET_ID=<id da planilha>

Uso:
    python manage.py exportar_sheets
"""

from __future__ import annotations

import os

from django.conf import settings


class SheetsIndisponivel(RuntimeError):
    pass


ESCOPOS = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _credenciais():
    """Carrega a service account de uma das duas fontes, nesta ordem:

    1. GOOGLE_SERVICE_ACCOUNT_JSON  -> o JSON inteiro colado numa variável de
       ambiente (recomendado no Render, que não tem arquivos persistentes).
    2. GOOGLE_SERVICE_ACCOUNT_FILE  -> caminho de um arquivo .json (dev local).
    """
    import json

    from google.oauth2.service_account import Credentials

    blob = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if blob:
        try:
            info = json.loads(blob)
        except json.JSONDecodeError as exc:
            raise SheetsIndisponivel(
                "GOOGLE_SERVICE_ACCOUNT_JSON não é um JSON válido."
            ) from exc
        return Credentials.from_service_account_info(info, scopes=ESCOPOS)

    caminho = settings.GOOGLE_SERVICE_ACCOUNT_FILE
    if caminho and os.path.exists(caminho):
        return Credentials.from_service_account_file(caminho, scopes=ESCOPOS)

    raise SheetsIndisponivel(
        "Credenciais do Google não encontradas. Defina GOOGLE_SERVICE_ACCOUNT_JSON "
        "(conteúdo do JSON) ou GOOGLE_SERVICE_ACCOUNT_FILE (caminho do arquivo)."
    )


def _client():
    try:
        import gspread
    except ImportError as exc:  # pragma: no cover
        raise SheetsIndisponivel(
            "Pacote gspread não instalado. Rode: pip install -r requirements.txt"
        ) from exc

    if not settings.GOOGLE_SHEETS_SPREADSHEET_ID:
        raise SheetsIndisponivel("GOOGLE_SHEETS_SPREADSHEET_ID não configurado.")

    return gspread.authorize(_credenciais())


def abrir_planilha(cliente_gs=None):
    """Abre a planilha configurada, com mensagens de erro claras."""
    import gspread

    cliente_gs = cliente_gs or _client()
    sid = (settings.GOOGLE_SHEETS_SPREADSHEET_ID or "").strip()
    try:
        return cliente_gs.open_by_key(sid)
    except gspread.exceptions.SpreadsheetNotFound as exc:
        raise SheetsIndisponivel(
            f"Planilha não encontrada (ID '{sid}'). Verifique se o "
            "GOOGLE_SHEETS_SPREADSHEET_ID é só o trecho entre /d/ e /edit da URL "
            "e se a planilha foi compartilhada como Editor com o e-mail da service "
            "account (campo client_email do JSON)."
        ) from exc
    except gspread.exceptions.APIError as exc:
        codigo = getattr(getattr(exc, "response", None), "status_code", "?")
        if codigo == 404:
            raise SheetsIndisponivel(
                f"Planilha não encontrada / sem acesso (ID '{sid}'). Confira o "
                "GOOGLE_SHEETS_SPREADSHEET_ID e o compartilhamento com a service "
                "account."
            ) from exc
        if codigo == 403:
            raise SheetsIndisponivel(
                "Acesso negado (403). Ative a Google Sheets API e a Google Drive "
                "API no projeto do Google Cloud e confirme o compartilhamento."
            ) from exc
        raise SheetsIndisponivel(f"Erro da API do Google Sheets: {exc}") from exc


def _escrever_aba(planilha, titulo, cabecalho, linhas):
    try:
        aba = planilha.worksheet(titulo)
        aba.clear()
    except Exception:
        aba = planilha.add_worksheet(title=titulo, rows=max(len(linhas) + 10, 20),
                                     cols=max(len(cabecalho), 10))
    aba.update([cabecalho] + [[_texto(c) for c in linha] for linha in linhas])


def _texto(valor):
    if valor is None:
        return ""
    return str(valor)


def exportar_tudo():
    """Exporta Clientes, Produtos e Pedidos para a planilha configurada.
    Retorna um resumo com a contagem de linhas por aba."""
    from apps.catalogo.models import Produto
    from apps.crm.models import Cliente
    from apps.vendas.models import Pedido

    planilha = abrir_planilha()

    clientes = [
        [c.nome, c.email, c.telefone, c.whatsapp, c.curso, c.periodo, c.campus,
         c.cidade, c.categoria.nome if c.categoria else "",
         c.get_relacionamento_display(), c.origem]
        for c in Cliente.objects.select_related("categoria")
    ]
    _escrever_aba(planilha, "Clientes",
                  ["Nome", "E-mail", "Telefone", "WhatsApp", "Curso", "Período",
                   "Campus", "Cidade", "Categoria", "Relacionamento", "Origem"],
                  clientes)

    produtos = [
        [p.nome, p.sku, p.categoria.nome if p.categoria else "", p.quantidade_atual,
         p.estoque_minimo, p.custo_unitario, p.preco_venda, p.get_status_display()]
        for p in Produto.objects.select_related("categoria")
    ]
    _escrever_aba(planilha, "Produtos",
                  ["Nome", "SKU", "Categoria", "Saldo", "Estoque mínimo",
                   "Custo", "Preço", "Status"], produtos)

    pedidos = [
        [p.numero, p.cliente.nome, p.data_compra, p.get_status_display(),
         p.get_status_pagamento_display(), p.valor_total, p.get_forma_pagamento_display()]
        for p in Pedido.objects.select_related("cliente")
    ]
    _escrever_aba(planilha, "Pedidos",
                  ["Número", "Cliente", "Data", "Status", "Pagamento", "Total",
                   "Forma"], pedidos)

    return {
        "Clientes": len(clientes),
        "Produtos": len(produtos),
        "Pedidos": len(pedidos),
    }
