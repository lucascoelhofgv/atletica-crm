"""Única tela server-rendered de vendas que sobrou: o recibo para impressão."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import Pedido


@login_required
def pedido_recibo(request, pk):
    pedido = get_object_or_404(Pedido.objects.select_related("cliente"), pk=pk)
    return render(request, "vendas/pedido_recibo.html", {
        "pedido": pedido,
        "itens": pedido.itens.select_related("produto"),
    })
