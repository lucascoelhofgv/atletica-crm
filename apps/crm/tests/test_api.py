from decimal import Decimal

import pytest

from apps.contas.models import PERFIL_ESTOQUE, PERFIL_OPERACIONAL, PERFIL_VISUALIZACAO
from apps.crm.models import CategoriaCliente, Cliente, Tag
from apps.nucleo.models import RegistroAtividade
from apps.vendas.models import Pedido

pytestmark = pytest.mark.django_db


@pytest.fixture
def base(db):
    aluno = CategoriaCliente.objects.create(nome="Aluno FGV")
    vip = Tag.objects.create(nome="VIP")
    ana = Cliente.objects.create(nome="Ana Prado", email="ana@x.test", curso="ADM",
                                 categoria=aluno, relacionamento="ativo")
    ana.tags.add(vip)
    bia = Cliente.objects.create(nome="Bia Souza", email="bia@x.test", membro_fgv=False)
    Pedido.objects.create(cliente=ana, status=Pedido.Status.PAGO, valor_total=Decimal("100"))
    Pedido.objects.create(cliente=ana, status=Pedido.Status.CANCELADO, valor_total=Decimal("999"))
    return {"aluno": aluno, "vip": vip, "ana": ana, "bia": bia}


def test_lista_busca_e_filtros(api_admin, base):
    r = api_admin.get("/api/clientes/")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["total"] == 2
    ana = next(c for c in corpo["resultados"] if c["nome"] == "Ana Prado")
    assert ana["categoria"]["nome"] == "Aluno FGV"
    assert ana["tags"][0]["nome"] == "VIP"
    assert ana["qtd_pedidos"] == 1 and ana["total_gasto"] == 100

    assert api_admin.get("/api/clientes/?q=bia").json()["total"] == 1
    assert api_admin.get("/api/clientes/?q=ADM").json()["total"] == 1
    assert api_admin.get(f"/api/clientes/?categoria={base['aluno'].id}").json()["total"] == 1
    assert api_admin.get("/api/clientes/?fgv=true").json()["total"] == 1
    assert api_admin.get(f"/api/clientes/?tag={base['vip'].id}").json()["total"] == 1
    assert api_admin.get("/api/clientes/?ordenar=-total_gasto_calc").json()["resultados"][0]["nome"] == "Ana Prado"


def test_detalhe(api_admin, base):
    d = api_admin.get(f"/api/clientes/{base['ana'].id}/").json()
    assert d["nome"] == "Ana Prado"
    assert d["total_gasto"] == 100 and d["qtd_pedidos"] == 1
    assert len(d["pedidos_recentes"]) == 2
    assert d["interacoes"] == []


def test_criar_editar_excluir(api_admin, base, admin):
    r = api_admin.post("/api/clientes/", {
        "nome": "  Caio Lima ", "email": "caio@x.test", "categoria_id": base["aluno"].id,
        "tags_ids": [base["vip"].id], "vinculo": "ex_aluno",
    }, format="json")
    assert r.status_code == 201, r.content
    d = r.json()
    assert d["nome"] == "Caio Lima" and d["categoria"]["id"] == base["aluno"].id
    assert [t["id"] for t in d["tags"]] == [base["vip"].id]
    assert d["criado_por"]["id"] == admin.id
    assert RegistroAtividade.objects.filter(verbo="cadastrou cliente", url=f"/clientes/{d['id']}").exists()

    r = api_admin.patch(f"/api/clientes/{d['id']}/", {"relacionamento": "recorrente", "tags_ids": []}, format="json")
    assert r.status_code == 200 and r.json()["relacionamento"] == "recorrente" and r.json()["tags"] == []

    assert api_admin.delete(f"/api/clientes/{d['id']}/").status_code == 204
    assert not Cliente.objects.filter(pk=d["id"]).exists()


def test_validacao(api_admin, base):
    r = api_admin.post("/api/clientes/", {"nome": "   ", "email": "invalido"}, format="json")
    assert r.status_code == 400
    campos = r.json()["erro"]["campos"]
    assert "nome" in campos and "email" in campos


def test_permissoes(api, criar_membro, base):
    api.force_login(criar_membro(PERFIL_VISUALIZACAO))
    assert api.get("/api/clientes/").status_code == 200
    assert api.post("/api/clientes/", {"nome": "X"}, format="json").status_code == 403

    api.force_login(criar_membro(PERFIL_ESTOQUE))
    assert api.post("/api/clientes/", {"nome": "X"}, format="json").status_code == 403

    api.force_login(criar_membro(PERFIL_OPERACIONAL))
    assert api.post("/api/clientes/", {"nome": "X"}, format="json").status_code == 201
    assert api.delete(f"/api/clientes/{base['bia'].id}/").status_code == 403   # só admin exclui


def test_interacoes(api_admin, base):
    url = f"/api/clientes/{base['ana'].id}/interacoes/"
    r = api_admin.post(url, {"tipo": "whatsapp", "resumo": "Combinou retirada"}, format="json")
    assert r.status_code == 201, r.content
    assert r.json()["registrado_por"] is not None and r.json()["data"]
    assert len(api_admin.get(url).json()) == 1
    assert api_admin.post(url, {"tipo": "x", "resumo": ""}, format="json").status_code == 400
    iid = r.json()["id"]
    assert api_admin.delete(f"{url}{iid}/").status_code == 204
    assert api_admin.get(url).json() == []


def test_opcoes_e_csv(api_admin, base):
    o = api_admin.get("/api/clientes/opcoes/").json()
    assert o["categorias"][0]["nome"] == "Aluno FGV" and o["tags"][0]["nome"] == "VIP"
    assert {"valor": "aluno", "rotulo": "Aluno FGV"} in o["vinculos"]
    r = api_admin.get("/api/clientes/exportar/?q=ana")
    assert r["Content-Type"].startswith("text/csv")
    linhas = r.content.decode("utf-8-sig").splitlines()
    assert len(linhas) == 2 and linhas[1].startswith("Ana Prado;")
