import pytest

from apps.catalogo.models import MovimentacaoEstoque, Produto
from apps.contas.models import PERFIL_FINANCEIRO, PERFIL_OPERACIONAL, PERFIL_VISUALIZACAO
from apps.crm.models import Cliente
from apps.vendas.models import Pedido

pytestmark = pytest.mark.django_db


@pytest.fixture
def base(db):
    ana = Cliente.objects.create(nome="Ana", email="ana@x.test")
    camiseta = Produto.objects.create(nome="Camiseta", tamanho="M", custo_unitario=30,
                                      preco_venda=80, quantidade_atual=10, estoque_minimo=2)
    bone = Produto.objects.create(nome="Boné", custo_unitario=20, preco_venda=50,
                                  quantidade_atual=1, estoque_minimo=2)
    return {"ana": ana, "camiseta": camiseta, "bone": bone}


def saldo(p):
    p.refresh_from_db()
    return p.quantidade_atual


def test_criar_rascunho_nao_mexe_no_estoque(api_admin, base):
    r = api_admin.post("/api/pedidos/", {
        "cliente": base["ana"].id,
        "itens": [{"produto": base["camiseta"].id, "quantidade": 2}],
    }, format="json")
    assert r.status_code == 201, r.content
    d = r.json()
    assert d["status"] == "rascunho" and not d["numero"]
    assert d["itens"][0]["preco_unitario"] == 80        # preço puxado do produto
    assert d["subtotal"] == 160 and d["valor_total"] == 160
    assert d["estoque_baixado"] is False
    assert saldo(base["camiseta"]) == 10


def test_pago_baixa_uma_vez_e_cancelar_estorna(api_admin, base):
    r = api_admin.post("/api/pedidos/", {
        "cliente": base["ana"].id, "status": "pago", "forma_pagamento": "pix",
        "desconto": "10", "itens": [{"produto": base["camiseta"].id, "quantidade": 3}],
    }, format="json")
    assert r.status_code == 201, r.content
    d = r.json()
    assert d["numero"].startswith("20") and d["estoque_baixado"] is True
    assert d["valor_total"] == 230 and saldo(base["camiseta"]) == 7
    pid = d["id"]

    # editar campos sem itens: não baixa de novo
    r = api_admin.patch(f"/api/pedidos/{pid}/", {"local_retirada": "Sala"}, format="json")
    assert r.status_code == 200 and saldo(base["camiseta"]) == 7

    # mudar para pronto: continua baixado, sem nova movimentação
    r = api_admin.post(f"/api/pedidos/{pid}/status/", {"status": "pronto"}, format="json")
    assert r.status_code == 200 and r.json()["status"] == "pronto"
    assert saldo(base["camiseta"]) == 7
    assert MovimentacaoEstoque.objects.filter(pedido_id=pid).count() == 1

    # cancelar estorna
    r = api_admin.post(f"/api/pedidos/{pid}/status/", {"status": "cancelado"}, format="json")
    assert r.status_code == 200 and r.json()["estoque_baixado"] is False
    assert saldo(base["camiseta"]) == 10


def test_editar_itens_de_pedido_baixado_nao_duplica(api_admin, base):
    r = api_admin.post("/api/pedidos/", {
        "cliente": base["ana"].id, "status": "pago",
        "itens": [{"produto": base["camiseta"].id, "quantidade": 3}],
    }, format="json")
    pid = r.json()["id"]
    item_id = r.json()["itens"][0]["id"]
    assert saldo(base["camiseta"]) == 7

    r = api_admin.patch(f"/api/pedidos/{pid}/", {
        "itens": [{"id": item_id, "produto": base["camiseta"].id, "quantidade": 5}],
    }, format="json")
    assert r.status_code == 200, r.content
    assert saldo(base["camiseta"]) == 5                 # 10 - 5, não 10 - 3 - 5
    assert r.json()["estoque_baixado"] is True
    assert r.json()["valor_total"] == 400

    # troca o item por outro produto
    r = api_admin.patch(f"/api/pedidos/{pid}/", {
        "itens": [{"produto": base["bone"].id, "quantidade": 1}],
    }, format="json")
    assert r.status_code == 200, r.content
    assert saldo(base["camiseta"]) == 10 and saldo(base["bone"]) == 0
    assert len(r.json()["itens"]) == 1


def test_estoque_insuficiente_recusa(api_admin, base):
    r = api_admin.post("/api/pedidos/", {
        "cliente": base["ana"].id, "status": "pago",
        "itens": [{"produto": base["bone"].id, "quantidade": 3}],
    }, format="json")
    assert r.status_code == 400, r.content
    erro = r.json()["erro"]
    assert "insuficiente" in erro["mensagem"].lower()
    assert erro["campos"]["itens"][0]["disponivel"] == 1
    assert saldo(base["bone"]) == 1
    assert Pedido.objects.count() == 0                 # transação desfeita

    r = api_admin.post("/api/pedidos/", {"cliente": base["ana"].id, "status": "aguardando_pagamento",
                                          "itens": [{"produto": base["bone"].id, "quantidade": 3}]}, format="json")
    assert r.status_code == 201
    d = r.json()
    assert d["faltas"][0]["necessario"] == 3
    assert api_admin.post(f"/api/pedidos/{d['id']}/status/", {"status": "pago"}, format="json").status_code == 400


def test_pagamentos(api, api_admin, criar_membro, base):
    r = api_admin.post("/api/pedidos/", {"cliente": base["ana"].id, "status": "aguardando_pagamento",
                                          "itens": [{"produto": base["camiseta"].id, "quantidade": 1}]}, format="json")
    pid = r.json()["id"]
    r = api_admin.post(f"/api/pedidos/{pid}/pagamentos/", {"valor": "30", "forma": "pix"}, format="json")
    assert r.status_code == 201, r.content
    assert r.json()["status_pagamento"] == "parcial" and r.json()["saldo_devedor"] == 50
    r = api_admin.post(f"/api/pedidos/{pid}/pagamentos/", {"valor": "50", "forma": "dinheiro"}, format="json")
    assert r.json()["status_pagamento"] == "quitado" and r.json()["total_pago"] == 80
    pag_id = r.json()["pagamentos"][0]["id"]
    r = api_admin.delete(f"/api/pedidos/{pid}/pagamentos/{pag_id}/")
    assert r.status_code == 200 and r.json()["status_pagamento"] == "parcial"
    assert api_admin.post(f"/api/pedidos/{pid}/pagamentos/", {"valor": "0", "forma": "pix"}, format="json").status_code == 400

    api.force_login(criar_membro(PERFIL_OPERACIONAL))   # escreve pedido, não registra pagamento
    assert api.post(f"/api/pedidos/{pid}/pagamentos/", {"valor": "1", "forma": "pix"}, format="json").status_code == 403
    api.force_login(criar_membro(PERFIL_FINANCEIRO))
    assert api.post(f"/api/pedidos/{pid}/pagamentos/", {"valor": "1", "forma": "pix"}, format="json").status_code == 201


def test_lista_filtros_e_permissoes(api, api_admin, criar_membro, base):
    api_admin.post("/api/pedidos/", {"cliente": base["ana"].id, "status": "pago",
                                      "itens": [{"produto": base["camiseta"].id, "quantidade": 1}]}, format="json")
    api_admin.post("/api/pedidos/", {"cliente": base["ana"].id, "itens": []}, format="json")
    lista = api_admin.get("/api/pedidos/").json()
    assert lista["total"] == 2 and lista["resultados"][0]["cliente"]["nome"] == "Ana"
    assert api_admin.get("/api/pedidos/?status=pago").json()["total"] == 1
    assert api_admin.get("/api/pedidos/?q=camiseta").json()["total"] == 1
    assert api_admin.get("/api/pedidos/?q=ana").json()["total"] == 2
    o = api_admin.get("/api/pedidos/opcoes/").json()
    assert {"valor": "pix", "rotulo": "PIX"} in o["formas_pagamento"] and o["membros"]

    api.force_login(criar_membro(PERFIL_VISUALIZACAO))
    assert api.get("/api/pedidos/").status_code == 200
    assert api.post("/api/pedidos/", {"cliente": base["ana"].id}, format="json").status_code == 403


def test_excluir_pedido_baixado_estorna(api_admin, base):
    r = api_admin.post("/api/pedidos/", {"cliente": base["ana"].id, "status": "pago",
                                          "itens": [{"produto": base["camiseta"].id, "quantidade": 4}]}, format="json")
    assert saldo(base["camiseta"]) == 6
    assert api_admin.delete(f"/api/pedidos/{r.json()['id']}/").status_code == 204
    assert saldo(base["camiseta"]) == 10
