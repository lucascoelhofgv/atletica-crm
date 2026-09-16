import pytest

from apps.catalogo.importador_planilha import analisar, importar_tudo
from apps.catalogo.models import Produto
from apps.crm.models import Cliente
from apps.vendas.models import Pedido

pytestmark = pytest.mark.django_db

GRID_PRODUTOS = [
    ["ATLÉTICA FGV RIO | CADASTRO DE PRODUTOS"],
    ["ID", "Categoria", "Produto", "Fornecedor", "Custo Unitário (R$)", "Preço de Venda (R$)",
     "Estoque Mínimo (un)", "Estoque Atual (un)", "Status do Estoque"],
    ["P01", "Brindes", "Caneca (Semestre)", "A definir", "R$ 16.78", "", "10", "16", "OK"],
    ["P02", "Vestuário", "Camisas", "A definir", "R$ 31.00", "", "10", "23", "OK"],
]

GRID_PEDIDOS = [
    ["ATLÉTICA FGV RIO | PEDIDOS — COMPRAS E ENTRADAS DE ESTOQUE"],
    ["ID", "Mês", "Descrição Original", "Produto", "Quantidade (un)", "Custo Unitário (R$)",
     "Status", "Observações"],
    ["PD01", "Julho", "Pedido de Canecas", "Caneca (Semestre)", "20", "R$ 16.78", "Recebido", ""],
    ["PD02", "Agosto", "Pedido de Camisas", "Camisas", "30", "R$ 31.00", "Planejado", "ainda não chegou"],
]

GRID_VENDAS = [
    ["ATLÉTICA FGV RIO | VENDAS — REGISTRO POR EVENTO"],
    ["ID", "Mês", "Data", "Evento", "Produto", "Quantidade Vendida (un)", "Preço Unit. (R$)"],
    ["EX", "—", "17/08/2026", "Moletons", "10", "", "-"],  # linha de exemplo, sem preço -> ignorada
    ["VD01", "", "17/08/2026", "Venda de Camisa", "Camisas", "4", "R$ 55.00"],
    ["VD02", "", "28/08/2026", "Venda de Canecas", "Caneca (Semestre)", "4", "R$ 45.00"],
]


def test_analisar_conta_certo_ignorando_placeholders():
    resumo = analisar(GRID_PRODUTOS, GRID_PEDIDOS, GRID_VENDAS)
    assert resumo == {
        "produtos": 2, "compras_total": 2, "compras_recebidas": 1, "vendas": 2,
    }


def test_importar_produtos_compras_e_vendas():
    resultado = importar_tudo(GRID_PRODUTOS, GRID_PEDIDOS, GRID_VENDAS)

    assert resultado["produtos"]["criados"] == 2
    assert resultado["compras"]["criados"] == 1   # só a "Recebido" vira movimentação
    assert resultado["vendas"]["criados"] == 2    # "EX" (sem preço) foi ignorada

    caneca = Produto.objects.get(nome="Caneca (Semestre)")
    camisas = Produto.objects.get(nome="Camisas")

    # caneca: 20 recebidos - 4 vendidos = 16
    assert caneca.quantidade_atual == 16
    assert caneca.preco_venda == 45  # veio da venda, já que a aba não tinha preço

    # camisas: pedido ainda "Planejado" não deu entrada -> saldo negativo é
    # esperado (reflete uma inconsistência real da planilha de origem)
    assert camisas.quantidade_atual == -4

    cliente = Cliente.objects.get(nome="Venda Stand")
    assert Pedido.objects.filter(cliente=cliente).count() == 2
    pedido_camisa = Pedido.objects.get(observacoes__icontains="venda VD01")
    assert pedido_camisa.valor_total == 220
    assert pedido_camisa.status == Pedido.Status.ENTREGUE


def test_reimportar_e_idempotente():
    importar_tudo(GRID_PRODUTOS, GRID_PEDIDOS, GRID_VENDAS)
    resultado2 = importar_tudo(GRID_PRODUTOS, GRID_PEDIDOS, GRID_VENDAS)

    assert resultado2["produtos"]["criados"] == 0
    assert resultado2["compras"]["criados"] == 0
    assert resultado2["vendas"]["criados"] == 0
    assert Pedido.objects.filter(cliente__nome="Venda Stand").count() == 2
