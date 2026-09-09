import csv
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from apps.catalogo.models import Produto
from apps.crm.models import Cliente
from apps.vendas.models import ItemPedido, Pedido

DEC = DecimalField(max_digits=12, decimal_places=2)


def _periodo(request):
    hoje = timezone.localdate()
    try:
        ini = request.GET.get("inicio") or str(hoje - timedelta(days=30))
        fim = request.GET.get("fim") or str(hoje)
    except Exception:
        ini, fim = str(hoje - timedelta(days=30)), str(hoje)
    return ini, fim


def _csv(nome, cabecalho, linhas):
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = f'attachment; filename="{nome}.csv"'
    w = csv.writer(resp)
    w.writerow(cabecalho)
    w.writerows(linhas)
    return resp


@login_required
def indice(request):
    return render(request, "relatorios/indice.html")


@login_required
def vendas_periodo(request):
    ini, fim = _periodo(request)
    qs = Pedido.objects.filter(data_compra__range=(ini, fim)).exclude(
        status__in=[Pedido.Status.RASCUNHO, Pedido.Status.CANCELADO]
    )
    por_dia = (
        qs.values("data_compra")
        .annotate(total=Coalesce(Sum("valor_total"), Value(0), output_field=DEC),
                  qtd=Count("id"))
        .order_by("data_compra")
    )
    if request.GET.get("formato") == "csv":
        return _csv("vendas_periodo", ["dia", "pedidos", "receita"],
                    [[r["data_compra"], r["qtd"], r["total"]] for r in por_dia])
    total = qs.aggregate(t=Coalesce(Sum("valor_total"), Value(0), output_field=DEC))["t"]
    return render(request, "relatorios/vendas_periodo.html", {
        "inicio": ini, "fim": fim, "por_dia": por_dia,
        "total": total, "qtd": qs.count(),
    })


@login_required
def produtos_vendidos(request):
    ini, fim = _periodo(request)
    dados = (
        ItemPedido.objects.filter(pedido__data_compra__range=(ini, fim))
        .exclude(pedido__status__in=[Pedido.Status.RASCUNHO, Pedido.Status.CANCELADO])
        .values("produto__nome")
        .annotate(
            qtd=Sum("quantidade"),
            receita=Coalesce(
                Sum(F("quantidade") * F("preco_unitario"), output_field=DEC),
                Value(0), output_field=DEC,
            ),
        )
        .order_by("-qtd")
    )
    if request.GET.get("formato") == "csv":
        return _csv("produtos_vendidos", ["produto", "quantidade", "receita"],
                    [[r["produto__nome"], r["qtd"], r["receita"]] for r in dados])
    return render(request, "relatorios/produtos_vendidos.html", {
        "inicio": ini, "fim": fim, "dados": dados,
    })


@login_required
def estoque_atual(request):
    produtos = Produto.objects.select_related("categoria").order_by("nome")
    if request.GET.get("situacao") == "baixo":
        produtos = produtos.filter(quantidade_atual__gt=0,
                                   quantidade_atual__lte=F("estoque_minimo"))
    elif request.GET.get("situacao") == "esgotado":
        produtos = produtos.filter(quantidade_atual__lte=0)
    if request.GET.get("formato") == "csv":
        return _csv(
            "estoque_atual",
            ["produto", "categoria", "saldo", "minimo", "valor_em_estoque"],
            [[p.nome, p.categoria.nome if p.categoria else "", p.quantidade_atual,
              p.estoque_minimo, p.valor_em_estoque] for p in produtos],
        )
    valor = sum((p.valor_em_estoque for p in produtos), 0)
    return render(request, "relatorios/estoque_atual.html", {
        "produtos": produtos, "valor": valor,
    })


@login_required
def clientes(request):
    dados = (
        Cliente.objects.annotate(qtd_pedidos=Count("pedidos"))
        .order_by("-qtd_pedidos", "nome")
    )
    if request.GET.get("recorrentes") == "1":
        dados = dados.filter(qtd_pedidos__gte=2)
    if request.GET.get("formato") == "csv":
        return _csv("clientes", ["nome", "email", "curso", "pedidos"],
                    [[c.nome, c.email, c.curso, c.qtd_pedidos] for c in dados])
    return render(request, "relatorios/clientes.html", {"dados": dados[:300]})
