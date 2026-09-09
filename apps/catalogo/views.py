import csv

from django.contrib import messages
from django.db.models import F, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from apps.contas.models import (
    PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_ESTOQUE, PERFIL_FINANCEIRO,
    PERFIL_OPERACIONAL,
)
from apps.nucleo.models import registrar_atividade
from apps.nucleo.permissoes import EscritaPerfilMixin, PerfilRequeridoMixin

from .forms import MovimentacaoForm, ProdutoForm
from .models import CategoriaProduto, MovimentacaoEstoque, Produto

LEITURA = [
    PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_OPERACIONAL, PERFIL_ESTOQUE,
    PERFIL_FINANCEIRO, "Visualização",
]
ESCRITA = [PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_ESTOQUE]


class ProdutoListView(PerfilRequeridoMixin, ListView):
    perfis_permitidos = LEITURA
    template_name = "catalogo/produto_lista.html"
    context_object_name = "produtos"
    paginate_by = 30

    def get_queryset(self):
        qs = Produto.objects.select_related("categoria", "fornecedor")
        p = self.request.GET
        if termo := p.get("q", "").strip():
            qs = qs.filter(
                Q(nome__icontains=termo) | Q(codigo_interno__icontains=termo)
                | Q(sku__icontains=termo) | Q(marca__icontains=termo)
            )
        if cat := p.get("categoria"):
            qs = qs.filter(categoria_id=cat)
        if p.get("situacao") == "baixo":
            qs = qs.filter(quantidade_atual__gt=0,
                           quantidade_atual__lte=F("estoque_minimo"))
        elif p.get("situacao") == "esgotado":
            qs = qs.filter(quantidade_atual__lte=0)
        return qs.order_by("nome")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categorias"] = CategoriaProduto.objects.filter(ativo=True)
        ctx["filtros"] = self.request.GET
        return ctx


class ProdutoDetailView(PerfilRequeridoMixin, DetailView):
    model = Produto
    perfis_permitidos = LEITURA
    template_name = "catalogo/produto_detalhe.html"
    context_object_name = "produto"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["movimentacoes"] = self.object.movimentacoes.select_related(
            "usuario", "pedido"
        )[:50]
        ctx["form_mov"] = MovimentacaoForm()
        return ctx


class ProdutoCreateView(EscritaPerfilMixin, CreateView):
    model = Produto
    perfis_permitidos = ESCRITA
    form_class = ProdutoForm
    template_name = "catalogo/produto_form.html"

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        resp = super().form_valid(form)
        registrar_atividade(
            self.request.user, "cadastrou produto", self.object.nome,
            url=self.object.get_absolute_url(),
        )
        messages.success(
            self.request,
            "Produto cadastrado. Use 'Movimentar estoque' para lançar o saldo inicial.",
        )
        return resp


class ProdutoUpdateView(EscritaPerfilMixin, UpdateView):
    model = Produto
    perfis_permitidos = ESCRITA
    form_class = ProdutoForm
    template_name = "catalogo/produto_form.html"

    def form_valid(self, form):
        resp = super().form_valid(form)
        registrar_atividade(
            self.request.user, "editou produto", self.object.nome,
            url=self.object.get_absolute_url(),
        )
        messages.success(self.request, "Produto atualizado.")
        return resp


class ProdutoDeleteView(EscritaPerfilMixin, DeleteView):
    model = Produto
    perfis_permitidos = [PERFIL_ADMIN]
    template_name = "confirmar_exclusao.html"
    success_url = reverse_lazy("catalogo:produto_lista")

    def form_valid(self, form):
        registrar_atividade(self.request.user, "excluiu produto", self.object.nome)
        messages.success(self.request, "Produto excluído.")
        return super().form_valid(form)


class MovimentacaoCreateView(EscritaPerfilMixin, CreateView):
    model = MovimentacaoEstoque
    perfis_permitidos = ESCRITA
    form_class = MovimentacaoForm

    def form_valid(self, form):
        produto = get_object_or_404(Produto, pk=self.kwargs["pk"])
        mov = form.save(commit=False)
        mov.produto = produto
        mov.usuario = self.request.user
        mov.save()
        registrar_atividade(
            self.request.user,
            f"movimentou estoque ({mov.get_tipo_display()})",
            f"{produto.nome} — {mov.quantidade} un.",
            url=produto.get_absolute_url(),
        )
        messages.success(
            self.request,
            f"Movimentação registrada. Saldo atual: {mov.saldo_apos} un.",
        )
        return redirect("catalogo:produto_detalhe", pk=produto.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Verifique os dados da movimentação.")
        return redirect("catalogo:produto_detalhe", pk=self.kwargs["pk"])


class MovimentacaoListView(PerfilRequeridoMixin, ListView):
    perfis_permitidos = LEITURA
    template_name = "catalogo/movimentacoes.html"
    context_object_name = "movimentacoes"
    paginate_by = 50

    def get_queryset(self):
        qs = MovimentacaoEstoque.objects.select_related("produto", "usuario", "pedido")
        if pid := self.request.GET.get("produto"):
            qs = qs.filter(produto_id=pid)
        if tipo := self.request.GET.get("tipo"):
            qs = qs.filter(tipo=tipo)
        return qs


def exportar_inventario(request):
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = 'attachment; filename="inventario.csv"'
    w = csv.writer(resp)
    w.writerow(["nome", "sku", "categoria", "saldo", "estoque_minimo",
                "custo_unitario", "preco_venda", "valor_em_estoque"])
    for p in Produto.objects.select_related("categoria"):
        w.writerow([p.nome, p.sku, p.categoria.nome if p.categoria else "",
                    p.quantidade_atual, p.estoque_minimo, p.custo_unitario,
                    p.preco_venda, p.valor_em_estoque])
    return resp
