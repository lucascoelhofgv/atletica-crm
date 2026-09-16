from datetime import timedelta

import pytest
from django.utils import timezone

from apps.contas.models import PERFIL_ESTOQUE, PERFIL_OPERACIONAL, PERFIL_VISUALIZACAO
from apps.eventos.models import Evento

pytestmark = pytest.mark.django_db


@pytest.fixture
def base(db):
    hoje = timezone.localdate()
    festa = Evento.objects.create(nome="Jungle 2026", tipo="festa", data=hoje + timedelta(days=30),
                                  local="Gávea", staff_cortesias=10, orcamento_previsto=5000)
    Evento.objects.create(nome="Churrasco", tipo="churrasco", data=hoje - timedelta(days=10), status="realizado")
    return {"festa": festa}


def test_lista_e_filtros(api_admin, base):
    d = api_admin.get("/api/eventos/").json()
    assert d["total"] == 2 and d["resultados"][0]["nome"] == "Jungle 2026"
    assert d["resultados"][0]["financeiro"]["receita_total"] == 0
    assert api_admin.get("/api/eventos/?tipo=festa").json()["total"] == 1
    assert api_admin.get("/api/eventos/?futuros=true").json()["total"] == 1
    assert api_admin.get("/api/eventos/?status=realizado").json()["total"] == 1
    assert api_admin.get("/api/eventos/?q=gávea").json()["total"] == 1


def test_pl_completo(api_admin, base):
    eid = base["festa"].id
    r = api_admin.post(f"/api/eventos/{eid}/lotes/", {"nome": "1º lote", "quantidade_prevista": 100,
                                                       "quantidade_vendida": 80, "valor_unitario": "50"}, format="json")
    assert r.status_code == 201, r.content
    r = api_admin.post(f"/api/eventos/{eid}/lotes/", {"nome": "Porta", "quantidade_prevista": 20,
                                                       "quantidade_vendida": 10, "valor_unitario": "100", "ordem": 2}, format="json")
    r = api_admin.post(f"/api/eventos/{eid}/custos/", {"tipo": "fixo", "item": "Local", "quantidade": "1",
                                                        "valor_unitario": "2000", "valor_pago": "1000", "situacao": "parcial"}, format="json")
    assert r.status_code == 201, r.content
    r = api_admin.post(f"/api/eventos/{eid}/custos/", {"tipo": "variavel", "item": "Bebidas", "quantidade": "100",
                                                        "valor_unitario": "5"}, format="json")
    r = api_admin.post(f"/api/eventos/{eid}/receitas/", {"origem": "patrocinio", "descricao": "Academia X",
                                                          "valor": "800", "recebido": True}, format="json")
    assert r.status_code == 201, r.content
    f = r.json()["financeiro"]
    assert f["ingressos_previstos"] == 120 and f["ingressos_vendidos"] == 90
    assert f["receita_ingressos"] == 5000 and f["receita_ingressos_prevista"] == 7000
    assert f["receita_extra"] == 800 and f["receita_total"] == 5800
    assert f["custo_total"] == 2500 and f["custo_pago"] == 1000 and f["custo_a_pagar"] == 1500
    assert f["resultado"] == 3300 and f["margem"] == pytest.approx(3300 / 5800)
    assert f["publico_estimado"] == 100 and f["custo_por_pessoa"] == 25
    assert f["ticket_medio"] == pytest.approx(5000 / 90)
    assert f["breakeven_ingressos"] == 31       # ceil((2500-800)/55.56)
    assert len(r.json()["lotes"]) == 2 and r.json()["lotes"][0]["total_vendido"] == 4000

    lote_id = r.json()["lotes"][0]["id"]
    r = api_admin.patch(f"/api/eventos/{eid}/lotes/{lote_id}/", {"quantidade_vendida": 100}, format="json")
    assert r.status_code == 200 and r.json()["financeiro"]["ingressos_vendidos"] == 110
    assert api_admin.patch(f"/api/eventos/{eid}/lotes/{lote_id}/", {"quantidade_vendida": 500}, format="json").status_code == 400
    r = api_admin.delete(f"/api/eventos/{eid}/lotes/{lote_id}/")
    assert r.status_code == 200 and len(r.json()["lotes"]) == 1
    assert api_admin.delete(f"/api/eventos/{eid}/lotes/9999/").status_code == 404


def test_crud_evento(api_admin, base):
    r = api_admin.post("/api/eventos/", {"nome": " FRAT HOUSE ", "tipo": "festa", "data": "2026-11-20",
                                          "capacidade": 300, "orcamento_previsto": "8000"}, format="json")
    assert r.status_code == 201, r.content
    eid = r.json()["id"]
    assert r.json()["nome"] == "FRAT HOUSE" and r.json()["status"] == "planejamento"
    r = api_admin.patch(f"/api/eventos/{eid}/", {"status": "confirmado", "publico_realizado": 250}, format="json")
    assert r.json()["status"] == "confirmado" and r.json()["financeiro"]["publico_estimado"] == 250
    o = api_admin.get("/api/eventos/opcoes/").json()
    assert {"valor": "festa", "rotulo": "Festa"} in o["tipos"] and o["origens_receita"]
    assert api_admin.delete(f"/api/eventos/{eid}/").status_code == 204


def test_permissoes(api, criar_membro, base):
    eid = base["festa"].id
    api.force_login(criar_membro(PERFIL_VISUALIZACAO))
    assert api.get("/api/eventos/").status_code == 200
    assert api.post(f"/api/eventos/{eid}/custos/", {"item": "x"}, format="json").status_code == 403
    api.force_login(criar_membro(PERFIL_ESTOQUE))
    assert api.post("/api/eventos/", {"nome": "X", "data": "2026-10-01"}, format="json").status_code == 403
    api.force_login(criar_membro(PERFIL_OPERACIONAL))
    assert api.post(f"/api/eventos/{eid}/receitas/", {"descricao": "Bar", "valor": "10"}, format="json").status_code == 201
    assert api.delete(f"/api/eventos/{eid}/").status_code == 403
