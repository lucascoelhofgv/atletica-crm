from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from apps.contas.models import (
    PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_FINANCEIRO, PERFIL_OPERACIONAL,
)
from apps.nucleo.models import registrar_atividade
from apps.nucleo.permissoes import PerfilRequeridoMixin

from .forms import ItemPedidoFormSet, PagamentoForm, PedidoForm
from .models import Pedido

LEITURA = [PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_OPERACIONAL, PERFIL_FINANCEIRO,
           "Estoque", "Visualização"]
ESCRITA = [PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_OPERACIONAL]


def _pode_escrever(user):
    return user.is_superuser or bool(set(ESCRITA) & set(user.perfis))


class PedidoListView(PerfilRequeridoMixin, ListView):
    perfis_permitidos = LEITURA
    template_name = "vendas/pedido_lista.html"
    context_object_name = "pedidos"
    paginate_by = 30

    def get_queryset(self):
        qs = Pedido.objects.select_related("cliente", "responsavel")
        p = self.request.GET
        if termo := p.get("q", "").strip():
            qs = qs.filter(
                Q(numero__icontains=termo) | Q(cliente__nome__icontains=termo)
                | Q(itens__produto__nome__icontains=termo)
            ).distinct()
        if status := p.get("status"):
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = Pedido.Status.choices
        ctx["filtros"] = self.request.GET
        ctx["pode_escrever"] = _pode_escrever(self.request.user)
        return ctx


class PedidoDetailView(PerfilRequeridoMixin, DetailView):
    model = Pedido
    perfis_permitidos = LEITURA
    template_name = "vendas/pedido_detalhe.html"
    context_object_name = "pedido"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["itens"] = self.object.itens.select_related("produto")
        ctx["pagamentos"] = self.object.pagamentos.select_related("registrado_por")
        ctx["form_pagamento"] = PagamentoForm()
        ctx["status_choices"] = Pedido.Status.choices
        ctx["faltas"] = self.object.itens_sem_estoque()
        ctx["pode_escrever"] = _pode_escrever(self.request.user)
        return ctx


def _editar_pedido(request, pedido):
    if not _pode_escrever(request.user):
        messages.error(request, "Sem permissão para lançar pedidos.")
        return redirect("vendas:pedido_lista")

    if request.method == "POST":
        form = PedidoForm(request.POST, request.FILES, instance=pedido)
        formset = ItemPedidoFormSet(request.POST, instance=pedido)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                novo = pedido.pk is None
                pedido = form.save(commit=False)
                if novo:
                    pedido.criado_por = request.user
                pedido.save()
                formset.instance = pedido
                formset.save()
                pedido.recalcular_total()
                pedido.aplicar_efeito_estoque(usuario=request.user)
            registrar_atividade(
                request.user,
                "criou pedido" if novo else "editou pedido",
                pedido.numero or f"rascunho #{pedido.pk}",
                url=pedido.get_absolute_url(),
            )
            messages.success(request, "Pedido salvo.")
            return redirect("vendas:pedido_detalhe", pk=pedido.pk)
        messages.error(request, "Confira os campos destacados.")
    else:
        form = PedidoForm(instance=pedido)
        formset = ItemPedidoFormSet(instance=pedido)

    return render(request, "vendas/pedido_form.html",
                  {"form": form, "formset": formset, "pedido": pedido})


def pedido_novo(request):
    return _editar_pedido(request, Pedido())


def pedido_editar(request, pk):
    return _editar_pedido(request, get_object_or_404(Pedido, pk=pk))


def mudar_status(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if request.method != "POST" or not _pode_escrever(request.user):
        return redirect("vendas:pedido_detalhe", pk=pk)

    novo = request.POST.get("status")
    if novo not in dict(Pedido.Status.choices):
        messages.error(request, "Status inválido.")
        return redirect("vendas:pedido_detalhe", pk=pk)

    if novo in Pedido.STATUS_BAIXA and not pedido.estoque_baixado:
        faltas = pedido.itens_sem_estoque()
        if faltas:
            nomes = ", ".join(f"{p.nome} (tem {s}, precisa {q})"
                              for p, q, s in faltas)
            messages.error(
                request,
                f"Estoque insuficiente para confirmar o pedido: {nomes}.",
            )
            return redirect("vendas:pedido_detalhe", pk=pk)

    with transaction.atomic():
        pedido.status = novo
        pedido.save()
        pedido.aplicar_efeito_estoque(usuario=request.user)
    registrar_atividade(
        request.user, "mudou status do pedido",
        f"{pedido.numero} → {pedido.get_status_display()}",
        url=pedido.get_absolute_url(),
    )
    messages.success(request, f"Pedido agora está: {pedido.get_status_display()}.")
    return redirect("vendas:pedido_detalhe", pk=pk)


def registrar_pagamento(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    pode_financeiro = request.user.is_superuser or bool(
        {PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_FINANCEIRO} & set(request.user.perfis)
    )
    if request.method != "POST" or not pode_financeiro:
        messages.error(request, "Sem permissão para registrar pagamentos.")
        return redirect("vendas:pedido_detalhe", pk=pk)

    form = PagamentoForm(request.POST)
    if form.is_valid():
        pag = form.save(commit=False)
        pag.pedido = pedido
        pag.registrado_por = request.user
        pag.save()
        if pedido.saldo_devedor <= 0:
            pedido.status_pagamento = Pedido.StatusPagamento.QUITADO
        elif pedido.total_pago > 0:
            pedido.status_pagamento = Pedido.StatusPagamento.PARCIAL
        pedido.save(update_fields=["status_pagamento"])
        registrar_atividade(
            request.user, "registrou pagamento",
            f"{pedido.numero} — R$ {pag.valor}", url=pedido.get_absolute_url(),
        )
        messages.success(request, "Pagamento registrado.")
    else:
        messages.error(request, "Não foi possível registrar o pagamento.")
    return redirect("vendas:pedido_detalhe", pk=pk)


def pedido_recibo(request, pk):
    pedido = get_object_or_404(
        Pedido.objects.select_related("cliente"), pk=pk
    )
    return render(request, "vendas/pedido_recibo.html", {
        "pedido": pedido,
        "itens": pedido.itens.select_related("produto"),
    })
