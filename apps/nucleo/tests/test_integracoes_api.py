import pytest

from apps.contas.models import PERFIL_DIRETORIA
from apps.crm.models import Cliente
from apps.nucleo.services import integracoes

pytestmark = pytest.mark.django_db


def test_situacao_e_permissao(api, api_admin, criar_membro, settings):
    settings.GOOGLE_SHEETS_SPREADSHEET_ID = "abc123"
    d = api_admin.get("/api/integracoes/sheets/").json()
    assert d["configurado"] is True and d["url_planilha"].endswith("abc123/edit")
    assert {x["valor"] for x in d["destinos"]} == {"fornecedores", "clientes"}
    assert len(d["sugeridas"]) == 2
    api.force_login(criar_membro(PERFIL_DIRETORIA))
    assert api.get("/api/integracoes/sheets/").status_code == 403


def test_exportar_sem_configuracao(api_admin, settings):
    settings.GOOGLE_SHEETS_SPREADSHEET_ID = ""
    r = api_admin.post("/api/integracoes/sheets/exportar/")
    assert r.status_code == 503 and r.json()["erro"]["codigo"] == "sheets_indisponivel"


def test_exportar_ok(api_admin, monkeypatch):
    monkeypatch.setattr(integracoes, "exportar_tudo", lambda: {"Clientes": 3, "Produtos": 8, "Pedidos": 14})
    r = api_admin.post("/api/integracoes/sheets/exportar/")
    assert r.status_code == 200 and r.json()["resumo"]["Pedidos"] == 14


def test_previa_e_importacao(api_admin, monkeypatch):
    linhas = [{"nome": "Ana", "email": "ana@x.test"}, {"nome": "Bia", "email": ""}]
    monkeypatch.setattr(integracoes, "ler_aba", lambda planilha, aba=None: (linhas, ["nome", "email"]))
    r = api_admin.post("/api/integracoes/importar/previa/", {"planilha": "xyz", "destino": "clientes"}, format="json")
    assert r.status_code == 200, r.content
    assert r.json()["total_linhas"] == 2 and r.json()["amostra"][0] == ["Ana", "ana@x.test"]
    assert api_admin.post("/api/integracoes/importar/previa/", {"planilha": "xyz", "destino": "x"}, format="json").status_code == 400

    r = api_admin.post("/api/integracoes/importar/", {"planilha": "xyz", "destino": "clientes", "modo": "somente_criar"}, format="json")
    assert r.status_code == 200, r.content
    assert r.json()["criados"] == 2 and Cliente.objects.count() == 2
    r = api_admin.post("/api/integracoes/importar/", {"planilha": "xyz", "destino": "clientes", "modo": "somente_criar"}, format="json")
    assert r.json()["criados"] == 0 and r.json()["ignorados"] == 2
