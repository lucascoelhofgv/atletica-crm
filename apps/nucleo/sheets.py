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

    return gspread.authorize(_credenciais())


def extrair_id_planilha(valor):
    """Aceita um ID puro ou a URL completa do Google Sheets e devolve o ID."""
    import re

    valor = (valor or "").strip()
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9_-]+)", valor)
    if m:
        return m.group(1)
    return valor


def abrir_planilha(cliente_gs=None, sheet_id=None):
    """Abre uma planilha (a configurada, ou `sheet_id`) com erros claros."""
    import gspread

    cliente_gs = cliente_gs or _client()
    sid = extrair_id_planilha(sheet_id or settings.GOOGLE_SHEETS_SPREADSHEET_ID)
    if not sid:
        raise SheetsIndisponivel(
            "Nenhuma planilha indicada. Configure GOOGLE_SHEETS_SPREADSHEET_ID "
            "ou informe a URL/ID da planilha de origem."
        )
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
        if codigo == 400 and "office file" in str(exc).lower():
            # Excel guardado no Drive sem converter: a API do Sheets não abre,
            # então baixamos o arquivo e lemos com openpyxl.
            return abrir_excel(sid)
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


# --------------------------------------------------------------------------- #
# Planilhas Excel (.xlsx) guardadas no Drive
# --------------------------------------------------------------------------- #
# Muita planilha da diretoria é um .xlsx que alguém subiu no Drive e continua
# editando por lá, sem "Salvar como Planilhas Google". O gspread recusa esses
# arquivos ("must not be an Office file"). Converter cria um arquivo novo, com
# outro ID, e a diretoria seguiria editando o antigo. Por isso o CRM lê o .xlsx
# como ele está: baixa pela API do Drive e entrega a mesma grade de texto que
# o gspread entregaria, para os importadores não precisarem saber a diferença.


def _texto_celula(valor):
    """Formata como o Google Sheets mostra em pt-BR, que é o que os
    importadores já sabem ler: vírgula decimal, data dd/mm/aaaa."""
    import datetime as dt

    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "TRUE" if valor else "FALSE"
    if isinstance(valor, dt.datetime):
        if valor.time() == dt.time(0, 0):
            return valor.strftime("%d/%m/%Y")
        return valor.strftime("%d/%m/%Y %H:%M")
    if isinstance(valor, dt.date):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, dt.time):
        return valor.strftime("%H:%M")
    if isinstance(valor, float):
        if valor == int(valor):
            return str(int(valor))
        return repr(round(valor, 10)).replace(".", ",")
    return str(valor)


class AbaExcel:
    """Uma aba do .xlsx com a mesma interface que o gspread usa aqui."""

    def __init__(self, ws, indice):
        self._ws = ws
        self.title = ws.title
        self.id = indice
        self.oculta = ws.sheet_state != "visible"

    def get_all_values(self):
        linhas = [
            [_texto_celula(v) for v in linha]
            for linha in self._ws.iter_rows(values_only=True)
        ]
        # Igual ao Google: sem linhas vazias no fim e com todas as linhas da
        # mesma largura (a da coluna mais à direita que tem valor).
        while linhas and not any(linhas[-1]):
            linhas.pop()
        largura = max(
            (max((j + 1 for j, v in enumerate(l) if v), default=0) for l in linhas),
            default=0,
        )
        return [(l + [""] * largura)[:largura] for l in linhas]


class PlanilhaExcel:
    def __init__(self, livro, titulo=""):
        self.title = titulo
        self._abas = [AbaExcel(ws, i) for i, ws in enumerate(livro.worksheets)]

    def worksheets(self):
        return list(self._abas)

    def worksheet(self, titulo):
        import gspread

        for aba in self._abas:
            if aba.title == titulo:
                return aba
        # Tolera diferença de maiúsculas e espaços, comum em nome de aba.
        alvo = titulo.strip().lower()
        for aba in self._abas:
            if aba.title.strip().lower() == alvo:
                return aba
        raise gspread.exceptions.WorksheetNotFound(titulo)

    def get_worksheet_by_id(self, gid):
        # .xlsx não tem gid: quem chama cai na primeira aba.
        import gspread

        raise gspread.exceptions.WorksheetNotFound(str(gid))

    @property
    def sheet1(self):
        return self._abas[0]


def baixar_arquivo_drive(sid) -> bytes:
    """Conteúdo bruto de um arquivo do Drive, com a mesma credencial."""
    from google.auth.transport.requests import AuthorizedSession

    sessao = AuthorizedSession(_credenciais())
    resp = sessao.get(
        f"https://www.googleapis.com/drive/v3/files/{sid}",
        params={"alt": "media", "supportsAllDrives": "true"},
        timeout=60,
    )
    if resp.status_code in (403, 404):
        raise SheetsIndisponivel(
            f"Não consegui baixar o arquivo '{sid}' do Drive ({resp.status_code}). "
            "Confira se ele foi compartilhado com o e-mail da service account."
        )
    if resp.status_code != 200:
        raise SheetsIndisponivel(
            f"O Drive respondeu {resp.status_code} ao baixar o arquivo '{sid}'."
        )
    return resp.content


def abrir_excel(sid, conteudo: bytes | None = None):
    """Abre um .xlsx do Drive (ou os bytes dados) como PlanilhaExcel."""
    import io

    try:
        import openpyxl
    except ImportError as exc:  # pragma: no cover
        raise SheetsIndisponivel(
            "Pacote openpyxl não instalado. Rode: pip install -r requirements.txt"
        ) from exc

    if conteudo is None:
        conteudo = baixar_arquivo_drive(sid)
    try:
        # data_only: o valor calculado da fórmula, não o texto "=SOMA(...)".
        livro = openpyxl.load_workbook(io.BytesIO(conteudo), data_only=True)
    except Exception as exc:
        raise SheetsIndisponivel(
            f"O arquivo '{sid}' não é uma planilha Excel que eu consiga abrir."
        ) from exc
    return PlanilhaExcel(livro, titulo=sid)


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


def extrair_gid_planilha(valor):
    """Se `valor` for uma URL com '#gid=123' ou '?gid=123', devolve o gid (int).
    Uma URL colada do navegador aponta pra uma aba específica — sem isso a
    gente sempre cairia na primeira aba da planilha."""
    import re

    m = re.search(r"[?#&]gid=(\d+)", str(valor or ""))
    return int(m.group(1)) if m else None


def listar_abas(sheet_id):
    """Nomes das abas de uma planilha de origem."""
    planilha = abrir_planilha(sheet_id=sheet_id)
    return [w.title for w in planilha.worksheets()]


def _abrir_aba(planilha, aba, sheet_id_original):
    """Resolve a aba: pelo nome (se informado), senão pelo gid embutido na
    URL colada, senão a primeira aba da planilha."""
    if aba:
        return planilha.worksheet(aba)
    gid = extrair_gid_planilha(sheet_id_original)
    if gid is not None:
        try:
            return planilha.get_worksheet_by_id(gid)
        except Exception:
            pass
    return planilha.sheet1


def ler_grade(sheet_id, aba=None):
    """Devolve a aba inteira como matriz de strings (linhas x colunas). Usado
    pelos importadores que precisam ler blocos soltos (não uma tabela simples
    com cabeçalho único) — ex.: planilhas de festa Jungle/FRAT HOUSE."""
    planilha = abrir_planilha(sheet_id=sheet_id)
    ws = _abrir_aba(planilha, aba, sheet_id)
    return ws.get_all_values()


def ler_abas(sheet_id, incluir_ocultas=False):
    """``{nome da aba: grade}`` de todas as abas, abrindo a planilha uma vez só.
    Abas ocultas costumam ser versão antiga ou rascunho e ficam de fora."""
    planilha = abrir_planilha(sheet_id=sheet_id)
    grades = {}
    for ws in planilha.worksheets():
        oculta = getattr(ws, "oculta", None)
        if oculta is None:
            oculta = bool(getattr(ws, "isSheetHidden", False))
        if oculta and not incluir_ocultas:
            continue
        grades[ws.title] = ws.get_all_values()
    return grades


def ler_aba(sheet_id, aba=None):
    """Lê uma aba e devolve (lista de dicts, cabeçalho).

    A primeira linha não vazia vira o cabeçalho; as seguintes viram registros
    ``{coluna: valor}``. Linhas totalmente vazias são ignoradas.
    """
    planilha = abrir_planilha(sheet_id=sheet_id)
    ws = _abrir_aba(planilha, aba, sheet_id)
    matriz = ws.get_all_values()
    if not matriz:
        return [], []

    idx_cab = 0
    for i, linha in enumerate(matriz):
        if any((c or "").strip() for c in linha):
            idx_cab = i
            break
    cabecalho = [(c or "").strip() for c in matriz[idx_cab]]

    registros = []
    for linha in matriz[idx_cab + 1:]:
        if not any((c or "").strip() for c in linha):
            continue
        reg = {}
        for j, nome in enumerate(cabecalho):
            if not nome:
                continue
            reg[nome] = linha[j].strip() if j < len(linha) and linha[j] else ""
        registros.append(reg)
    return registros, [c for c in cabecalho if c]


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
