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


def _client():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError as exc:  # pragma: no cover
        raise SheetsIndisponivel(
            "Pacotes gspread/google-auth não instalados. Rode: pip install -r requirements.txt"
        ) from exc

    caminho = settings.GOOGLE_SERVICE_ACCOUNT_FILE
    if not caminho or not os.path.exists(caminho):
        raise SheetsIndisponivel(
            f"Arquivo de credenciais não encontrado: {caminho}"
        )
    if not settings.GOOGLE_SHEETS_SPREADSHEET_ID:
        raise SheetsIndisponivel("GOOGLE_SHEETS_SPREADSHEET_ID não configurado.")

    escopos = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    cred = Credentials.from_service_account_file(caminho, scopes=escopos)
    return gspread.authorize(cred)


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

    cliente_gs = _client()
    planilha = cliente_gs.open_by_key(settings.GOOGLE_SHEETS_SPREADSHEET_ID)

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
