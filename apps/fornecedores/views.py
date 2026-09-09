from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from apps.contas.models import (
    PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_ESTOQUE, PERFIL_FINANCEIRO,
)
from apps.nucleo.models import registrar_atividade
from apps.nucleo.permissoes import EscritaPerfilMixin, PerfilRequeridoMixin

from .forms import AvaliacaoForm, FornecedorForm
from .models import AvaliacaoFornecedor, Fornecedor

LEITURA = [PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_ESTOQUE, PERFIL_FINANCEIRO,
           "Operacional", "Visualização"]
ESCRITA = [PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_ESTOQUE]


class FornecedorListView(PerfilRequeridoMixin, ListView):
    perfis_permitidos = LEITURA
    template_name = "fornecedores/lista.html"
    context_object_name = "fornecedores"
    paginate_by = 25

    def get_queryset(self):
        qs = Fornecedor.objects.all()
        p = self.request.GET
        if termo := p.get("q", "").strip():
            qs = qs.filter(
                Q(nome__icontains=termo) | Q(nome_fantasia__icontains=termo)
                | Q(contato_nome__icontains=termo)
            )
        if cat := p.get("categoria"):
            qs = qs.filter(categoria=cat)
        return qs.order_by("nome")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categorias"] = Fornecedor.Categoria.choices
        ctx["filtros"] = self.request.GET
        return ctx


class FornecedorDetailView(PerfilRequeridoMixin, DetailView):
    model = Fornecedor
    perfis_permitidos = LEITURA
    template_name = "fornecedores/detalhe.html"
    context_object_name = "fornecedor"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["avaliacoes"] = self.object.avaliacoes.select_related("autor")
        ctx["produtos"] = self.object.produtos.all()[:50]
        ctx["form_avaliacao"] = AvaliacaoForm()
        return ctx


class FornecedorCreateView(EscritaPerfilMixin, CreateView):
    model = Fornecedor
    perfis_permitidos = ESCRITA
    form_class = FornecedorForm
    template_name = "fornecedores/form.html"

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        resp = super().form_valid(form)
        registrar_atividade(self.request.user, "cadastrou fornecedor",
                            self.object.nome, url=self.object.get_absolute_url())
        messages.success(self.request, "Fornecedor cadastrado.")
        return resp


class FornecedorUpdateView(EscritaPerfilMixin, UpdateView):
    model = Fornecedor
    perfis_permitidos = ESCRITA
    form_class = FornecedorForm
    template_name = "fornecedores/form.html"

    def form_valid(self, form):
        resp = super().form_valid(form)
        registrar_atividade(self.request.user, "editou fornecedor",
                            self.object.nome, url=self.object.get_absolute_url())
        messages.success(self.request, "Fornecedor atualizado.")
        return resp


class FornecedorDeleteView(EscritaPerfilMixin, DeleteView):
    model = Fornecedor
    perfis_permitidos = [PERFIL_ADMIN]
    template_name = "confirmar_exclusao.html"
    success_url = reverse_lazy("fornecedores:lista")

    def form_valid(self, form):
        registrar_atividade(self.request.user, "excluiu fornecedor", self.object.nome)
        messages.success(self.request, "Fornecedor excluído.")
        return super().form_valid(form)


class AvaliacaoCreateView(EscritaPerfilMixin, CreateView):
    model = AvaliacaoFornecedor
    perfis_permitidos = ESCRITA
    form_class = AvaliacaoForm

    def form_valid(self, form):
        form.instance.fornecedor = get_object_or_404(
            Fornecedor, pk=self.kwargs["pk"]
        )
        form.instance.autor = self.request.user
        form.save()
        messages.success(self.request, "Avaliação registrada.")
        return redirect("fornecedores:detalhe", pk=self.kwargs["pk"])

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível registrar a avaliação.")
        return redirect("fornecedores:detalhe", pk=self.kwargs["pk"])
