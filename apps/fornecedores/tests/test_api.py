import pytest

from apps.catalogo.models import Produto
from apps.contas.models import PERFIL_ESTOQUE, PERFIL_OPERACIONAL, PERFIL_VISUALIZACAO
from apps.fornecedores.models import Fornecedor

pytestmark = pytest.mark.django_db


@pytest.fixture
def base(db):
    rio = Fornecedor.objects.create(nome="Uniformes Rio Ltda", nome_fantasia="RioSport",
                                    categoria="confeccao", contato_nome="Marina")
    dist = Fornecedor.objects.create(nome="Distribuidora Maracanã", categoria="bebidas", status="inativo")
    Produto.objects.create(nome="Camiseta", fornecedor=rio, custo_unitario=1, preco_venda=2)
    return {"rio": rio, "dist": dist}


def test_lista_busca_filtros(api_admin, base):
    d = api_admin.get("/api/fornecedores/").json()
    assert d["total"] == 2
    rio = next(f for f in d["resultados"] if f["nome_fantasia"] == "RioSport")
    assert rio["nome_exibicao"] == "RioSport" and rio["qtd_produtos"] == 1 and rio["nota_media"] is None
    assert api_admin.get("/api/fornecedores/?q=marina").json()["total"] == 1
    assert api_admin.get("/api/fornecedores/?categoria=bebidas").json()["total"] == 1
    assert api_admin.get("/api/fornecedores/?status=ativo").json()["total"] == 1


def test_crud_e_avaliacoes(api_admin, base):
    r = api_admin.post("/api/fornecedores/", {"nome": " Gráfica Central ", "categoria": "grafica",
                                               "email": "x@y.test"}, format="json")
    assert r.status_code == 201, r.content
    fid = r.json()["id"]
    assert r.json()["nome"] == "Gráfica Central"
    assert api_admin.patch(f"/api/fornecedores/{fid}/", {"status": "inativo"}, format="json").json()["status"] == "inativo"

    r = api_admin.post(f"/api/fornecedores/{fid}/avaliacoes/",
                       {"preco": 5, "qualidade": 4, "prazo": 3, "atendimento": 5, "confiabilidade": 3,
                        "comentario": "Ok"}, format="json")
    assert r.status_code == 201, r.content
    d = r.json()
    assert d["qtd_avaliacoes"] == 1 and d["nota_media"] == pytest.approx(4.0)
    assert d["avaliacoes"][0]["media"] == pytest.approx(4.0) and d["avaliacoes"][0]["autor"]
    assert api_admin.post(f"/api/fornecedores/{fid}/avaliacoes/", {"preco": 9}, format="json").status_code == 400
    aid = d["avaliacoes"][0]["id"]
    assert api_admin.delete(f"/api/fornecedores/{fid}/avaliacoes/{aid}/").json()["qtd_avaliacoes"] == 0

    assert api_admin.delete(f"/api/fornecedores/{fid}/").status_code == 204


def test_detalhe_lista_produtos(api_admin, base):
    d = api_admin.get(f"/api/fornecedores/{base['rio'].id}/").json()
    assert d["produtos"][0]["nome"] == "Camiseta"
    assert api_admin.get("/api/fornecedores/opcoes/").json()["categorias"][0]["valor"] == "confeccao"


def test_permissoes(api, criar_membro, base):
    fid = base["rio"].id
    api.force_login(criar_membro(PERFIL_VISUALIZACAO))
    assert api.get("/api/fornecedores/").status_code == 200
    assert api.post("/api/fornecedores/", {"nome": "X"}, format="json").status_code == 403
    api.force_login(criar_membro(PERFIL_OPERACIONAL))
    assert api.post("/api/fornecedores/", {"nome": "X"}, format="json").status_code == 403
    api.force_login(criar_membro(PERFIL_ESTOQUE))
    assert api.post("/api/fornecedores/", {"nome": "X"}, format="json").status_code == 201
    assert api.delete(f"/api/fornecedores/{fid}/").status_code == 403
