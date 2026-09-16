from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.catalogo.models import Produto
from apps.contas.models import PERFIL_VISUALIZACAO
from apps.crm.models import Cliente
from apps.vendas.models import ItemPedido, Pedido

pytestmark = pytest.mark.django_db


@pytest.fixture
def base(db):
    hoje = timezone.localdate()
    ana = Cliente.objects.create(nome="Ana", email="ana@x.test", curso="ADM")
    bia = Cliente.objects.create(nome="Bia", email="bia@x.test")
    camiseta = Produto.objects.create(nome="Camiseta", custo_unitario=30, preco_venda=80,
                                      quantidade_atual=10, estoque_minimo=5)
    bone = Produto.objects.create(nome="Boné", custo_unitario=20, preco_venda=50,
                                  quantidade_atual=2, estoque_minimo=5)
    Produto.objects.create(nome="Caneca", custo_unitario=10, preco_venda=30,
                           quantidade_atual=0, estoque_minimo=3)

    def pedido(cliente, dias, status, valor, itens=()):
        p = Pedido.objects.create(cliente=cliente, status=status, valor_total=Decimal(valor),
                                  data_compra=hoje - timedelta(days=dias),
                                  forma_pagamento=Pedido.FormaPagamento.PIX)
        for produto, qtd in itens:
            ItemPedido.objects.create(pedido=p, produto=produto, quantidade=qtd,
                                      preco_unitario=produto.preco_venda)
        return p

    pedido(ana, 0, Pedido.Status.PAGO, "160", [(camiseta, 2)])
    pedido(ana, 3, Pedido.Status.AGUARDANDO, "50", [(bone, 1)])   # vendido, não pago
    pedido(bia, 1, Pedido.Status.ENTREGUE, "80", [(camiseta, 1)])
    pedido(bia, 2, Pedido.Status.CANCELADO, "500", [(camiseta, 5)])  # ignorado
    pedido(ana, 10, Pedido.Status.PAGO, "80", [(camiseta, 1)])       # período anterior
    return hoje


def test_exige_login_e_perfil(api, criar_membro, base):
    assert api.get("/api/relatorios/vendas/").status_code == 401
    api.force_login(criar_membro(PERFIL_VISUALIZACAO))
    assert api.get("/api/relatorios/vendas/").status_code == 200  # leitura liberada


def test_vendas_periodo(api_admin, base):
    d = api_admin.get("/api/relatorios/vendas/?periodo=7d&comparar=1").json()
    assert d["total"] == 290 and d["qtd"] == 3
    assert d["ticket_medio"] == pytest.approx(96.67, abs=0.01)
    assert d["total_anterior"] == 80 and d["qtd_anterior"] == 1
    assert len(d["por_periodo"]) == 8
    assert d["por_periodo"][-1] == {"data": str(base), "total": 160, "qtd": 1,
                                    "anterior": 0, "qtd_anterior": 0}
    assert sum(l["total"] for l in d["por_periodo"]) == 290
    assert {s["status"] for s in d["por_status"]} >= {"pago", "cancelado"}


def test_vendas_csv(api_admin, base):
    r = api_admin.get("/api/relatorios/vendas/?periodo=7d&formato=csv")
    assert r.status_code == 200
    assert r["Content-Type"].startswith("text/csv")
    linhas = r.content.decode("utf-8-sig").strip().splitlines()
    assert linhas[0] == "dia;pedidos;receita"
    assert len(linhas) == 9


def test_produtos_vendidos(api_admin, base):
    d = api_admin.get("/api/relatorios/produtos/?periodo=7d").json()
    assert d["itens"][0]["produto"] == "Camiseta"
    assert d["itens"][0]["qtd"] == 3 and d["itens"][0]["receita"] == 240
    assert d["itens"][0]["pedidos"] == 2
    assert d["total_qtd"] == 4 and d["total_receita"] == 290
    assert d["itens"][0]["participacao"] == pytest.approx(240 / 290)
    assert d["periodo"]["chave"] == "7d"


def test_estoque(api_admin, base):
    d = api_admin.get("/api/relatorios/estoque/").json()
    assert d["resumo"] == {"ok": 1, "baixo": 1, "esgotado": 1}
    assert d["valor_total"] == 10 * 30 + 2 * 20
    assert "produtos" not in d
    baixo = api_admin.get("/api/relatorios/estoque/?situacao=baixo").json()
    assert [i["nome"] for i in baixo["itens"]] == ["Boné"]
    assert baixo["itens"][0]["situacao"] == "baixo"


def test_clientes(api_admin, base):
    d = api_admin.get("/api/relatorios/clientes/").json()
    assert d["itens"][0]["nome"] == "Ana"
    assert d["itens"][0]["pedidos"] == 3          # cancelados/rascunhos fora
    assert d["itens"][0]["gasto"] == 240          # só pago/entregue etc.
    bia = next(i for i in d["itens"] if i["nome"] == "Bia")
    assert bia["pedidos"] == 1 and bia["gasto"] == 80
    rec = api_admin.get("/api/relatorios/clientes/?recorrentes=1").json()
    assert [i["nome"] for i in rec["itens"]] == ["Ana"]
