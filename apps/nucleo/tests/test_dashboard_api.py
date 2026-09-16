from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.catalogo.models import Produto
from apps.crm.models import Cliente
from apps.vendas.models import ItemPedido, Pedido

pytestmark = pytest.mark.django_db


@pytest.fixture
def base_vendas(db):
    hoje = timezone.localdate()
    cliente = Cliente.objects.create(nome="Ana", email="ana@x.test")
    camiseta = Produto.objects.create(nome="Camiseta", custo_unitario=30, preco_venda=80)
    bone = Produto.objects.create(nome="Boné", custo_unitario=20, preco_venda=50)

    def pedido(dias_atras, status, valor, itens=()):
        p = Pedido.objects.create(
            cliente=cliente, status=status, valor_total=Decimal(valor),
            data_compra=hoje - timedelta(days=dias_atras),
            forma_pagamento=Pedido.FormaPagamento.PIX,
        )
        for produto, qtd in itens:
            ItemPedido.objects.create(pedido=p, produto=produto, quantidade=qtd,
                                      preco_unitario=produto.preco_venda)
        return p

    # período 7d (8 dias: hoje-7 .. hoje)
    pedido(0, Pedido.Status.PAGO, "100", [(camiseta, 1)])
    pedido(2, Pedido.Status.ENTREGUE, "300", [(camiseta, 2), (bone, 1)])
    pedido(3, Pedido.Status.AGUARDANDO, "50")        # conta em pedidos, não em receita
    pedido(4, Pedido.Status.CANCELADO, "999")         # ignorado
    pedido(5, Pedido.Status.RASCUNHO, "999")          # ignorado
    # período anterior (hoje-15 .. hoje-8)
    pedido(9, Pedido.Status.PAGO, "200")
    pedido(12, Pedido.Status.PAGO, "200")
    return hoje


def test_exige_login(api):
    assert api.get("/api/dashboard/").status_code == 401


def test_payload_7d_com_comparacao(api_admin, base_vendas):
    r = api_admin.get("/api/dashboard/?periodo=7d&comparar=1")
    assert r.status_code == 200, r.content
    d = r.json()

    assert d["periodo"]["chave"] == "7d"
    assert d["periodo"]["dias"] == 8
    assert d["periodo"]["granularidade"] == "dia"
    assert d["periodo"]["comparar"] is True

    kpis = d["kpis"]
    assert kpis["receita"]["valor"] == 400
    assert kpis["receita"]["anterior"] == 400
    assert kpis["receita"]["variacao"] == 0
    assert kpis["pedidos"]["valor"] == 3
    assert kpis["pedidos"]["anterior"] == 2
    assert kpis["pedidos"]["variacao"] == pytest.approx(0.5)
    assert kpis["ticket_medio"]["valor"] == 200
    assert len(kpis["receita"]["serie"]) == 8

    serie = d["series"]["receita"]
    assert len(serie) == 8
    assert serie[-1]["valor"] == 100          # hoje
    assert serie[-3]["valor"] == 300          # hoje-2
    assert sum(p["valor"] for p in serie) == 400
    assert all("anterior" in p for p in serie)
    assert sum(p["anterior"] for p in serie) == 400

    top = d["top_produtos"]
    assert top[0] == {"nome": "Camiseta", "qtd": 3, "receita": 240}
    assert d["status_pedidos"][0]["qtd"] >= 1
    assert d["formas_pagamento"][0]["forma"] == "pix"
    assert set(d["alertas"]) >= {"pedidos_aguardando", "produtos_baixo", "valor_estoque"}
    assert d["alertas"]["pedidos_aguardando"] == 1
    assert isinstance(d["atividades"], list) and isinstance(d["minhas_tarefas"], list)


def test_sem_comparacao_nao_traz_anterior(api_admin, base_vendas):
    d = api_admin.get("/api/dashboard/?periodo=7d").json()
    assert d["kpis"]["receita"]["anterior"] is None
    assert d["kpis"]["receita"]["variacao"] is None
    assert "anterior" not in d["series"]["receita"][0]


def test_variacao_com_anterior_zero(api_admin, base_vendas):
    d = api_admin.get("/api/dashboard/?periodo=hoje&comparar=1").json()
    assert d["kpis"]["receita"]["valor"] == 100
    assert d["kpis"]["receita"]["anterior"] == 0
    assert d["kpis"]["receita"]["variacao"] is None


def test_custom_longo_vira_mensal(api_admin, base_vendas):
    hoje = base_vendas
    inicio = (hoje - timedelta(days=200)).isoformat()
    d = api_admin.get(f"/api/dashboard/?periodo=custom&inicio={inicio}&fim={hoje}").json()
    assert d["periodo"]["granularidade"] == "mes"
    assert 6 <= len(d["series"]["receita"]) <= 8
    assert sum(p["valor"] for p in d["series"]["receita"]) == 800
