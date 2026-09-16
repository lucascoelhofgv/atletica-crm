import pytest

from apps.catalogo.models import CategoriaProduto, MovimentacaoEstoque, Produto
from apps.contas.models import PERFIL_ESTOQUE, PERFIL_OPERACIONAL, PERFIL_VISUALIZACAO
from apps.nucleo.models import RegistroAtividade

pytestmark = pytest.mark.django_db


@pytest.fixture
def base(db):
    vest = CategoriaProduto.objects.create(nome="Vestuário")
    camiseta = Produto.objects.create(nome="Camiseta", tamanho="M", categoria=vest,
                                      custo_unitario=30, preco_venda=80,
                                      quantidade_atual=10, estoque_minimo=5)
    bone = Produto.objects.create(nome="Boné", custo_unitario=20, preco_venda=50,
                                  quantidade_atual=2, estoque_minimo=5)
    caneca = Produto.objects.create(nome="Caneca", custo_unitario=10, preco_venda=30,
                                    quantidade_atual=0, estoque_minimo=3, status="inativo")
    return {"vest": vest, "camiseta": camiseta, "bone": bone, "caneca": caneca}


def test_lista_filtros_e_busca(api_admin, base):
    corpo = api_admin.get("/api/produtos/").json()
    assert corpo["total"] == 3
    cam = next(p for p in corpo["resultados"] if p["nome"] == "Camiseta")
    assert cam["nome_completo"] == "Camiseta · M"
    assert cam["situacao"] == "ok" and cam["valor_em_estoque"] == 300
    assert cam["margem_estimada"] == pytest.approx(0.625)

    assert api_admin.get("/api/produtos/?situacao=baixo").json()["resultados"][0]["nome"] == "Boné"
    assert api_admin.get("/api/produtos/?situacao=esgotado").json()["total"] == 1
    assert api_admin.get("/api/produtos/?status=ativo").json()["total"] == 2
    assert api_admin.get(f"/api/produtos/?categoria={base['vest'].id}").json()["total"] == 1
    assert api_admin.get("/api/produtos/?q=bon").json()["total"] == 1
    assert api_admin.get("/api/produtos/?ordenar=-quantidade_atual").json()["resultados"][0]["nome"] == "Camiseta"


def test_criar_editar_sem_mexer_no_saldo(api_admin, base):
    r = api_admin.post("/api/produtos/", {
        "nome": " Moletom ", "categoria_id": base["vest"].id, "custo_unitario": "90",
        "preco_venda": "189.90", "estoque_minimo": 8, "quantidade_atual": 999,
    }, format="json")
    assert r.status_code == 201, r.content
    d = r.json()
    assert d["nome"] == "Moletom" and d["categoria"]["nome"] == "Vestuário"
    assert d["quantidade_atual"] == 0            # saldo ignorado na criação
    assert d["situacao"] == "esgotado"
    assert RegistroAtividade.objects.filter(verbo="cadastrou produto", url=f"/produtos/{d['id']}").exists()

    r = api_admin.patch(f"/api/produtos/{d['id']}/", {"preco_venda": "199.90", "quantidade_atual": 50}, format="json")
    assert r.status_code == 200 and r.json()["preco_venda"] == 199.9 and r.json()["quantidade_atual"] == 0


def test_validacoes(api_admin, base):
    r = api_admin.post("/api/produtos/", {"nome": "X", "custo_unitario": "-1", "estoque_minimo": 10,
                                          "estoque_maximo": 5}, format="json")
    assert r.status_code == 400
    campos = r.json()["erro"]["campos"]
    assert "custo_unitario" in campos and "estoque_maximo" in campos


def test_movimentar(api_admin, base, admin):
    pid = base["camiseta"].id
    r = api_admin.post(f"/api/produtos/{pid}/movimentar/",
                       {"tipo": "entrada", "quantidade": 5, "motivo": "Compra"}, format="json")
    assert r.status_code == 201, r.content
    assert r.json()["movimentacao"]["saldo_apos"] == 15
    assert r.json()["produto"]["quantidade_atual"] == 15
    assert r.json()["movimentacao"]["usuario"]["id"] == admin.id

    r = api_admin.post(f"/api/produtos/{pid}/movimentar/", {"tipo": "perda", "quantidade": 20}, format="json")
    assert r.status_code == 201 and r.json()["produto"]["quantidade_atual"] == -5
    assert r.json()["produto"]["situacao"] == "esgotado"

    assert api_admin.post(f"/api/produtos/{pid}/movimentar/", {"tipo": "entrada", "quantidade": 0}, format="json").status_code == 400
    assert api_admin.post(f"/api/produtos/{pid}/movimentar/", {"tipo": "xyz", "quantidade": 1}, format="json").status_code == 400

    d = api_admin.get(f"/api/produtos/{pid}/").json()
    assert len(d["movimentacoes_recentes"]) == 2 and d["movimentacoes_recentes"][0]["tipo"] == "perda"

    lista = api_admin.get(f"/api/movimentacoes/?produto={pid}&tipo=entrada").json()
    assert lista["total"] == 1 and lista["resultados"][0]["produto_nome"] == "Camiseta · M"
    assert MovimentacaoEstoque.objects.count() == 2


def test_permissoes(api, criar_membro, base):
    pid = base["bone"].id
    api.force_login(criar_membro(PERFIL_VISUALIZACAO))
    assert api.get("/api/produtos/").status_code == 200
    assert api.post(f"/api/produtos/{pid}/movimentar/", {"tipo": "entrada", "quantidade": 1}, format="json").status_code == 403

    api.force_login(criar_membro(PERFIL_OPERACIONAL))   # lê catálogo, não escreve
    assert api.post("/api/produtos/", {"nome": "X"}, format="json").status_code == 403

    api.force_login(criar_membro(PERFIL_ESTOQUE))
    assert api.post(f"/api/produtos/{pid}/movimentar/", {"tipo": "entrada", "quantidade": 1}, format="json").status_code == 201
    assert api.delete(f"/api/produtos/{pid}/").status_code == 403


def test_opcoes_e_csv(api_admin, base):
    o = api_admin.get("/api/produtos/opcoes/").json()
    assert o["categorias"][0]["nome"] == "Vestuário"
    assert {"valor": "entrada", "rotulo": "Entrada de mercadoria"} in o["tipos_movimentacao"]
    r = api_admin.get("/api/produtos/exportar/?situacao=baixo")
    linhas = r.content.decode("utf-8-sig").splitlines()
    assert len(linhas) == 2 and linhas[1].startswith("Boné;")
