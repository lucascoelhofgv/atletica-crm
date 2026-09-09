import csv

from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from apps.contas.models import (
    PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_FINANCEIRO, PERFIL_OPERACIONAL,
)
from apps.nucleo.models import registrar_atividade
from apps.nucleo.permissoes import EscritaPerfilMixin, PerfilRequeridoMixin

from .forms import ClienteForm, ImportarClientesForm, InteracaoForm
from .models import CategoriaCliente, Cliente, Interacao

LEITURA = [
    PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_OPERACIONAL, PERFIL_FINANCEIRO,
    "Estoque", "Visualização",
]
ESCRITA = [PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_OPERACIONAL]


class ClienteListView(PerfilRequeridoMixin, ListView):
    model = Cliente
    perfis_permitidos = LEITURA
    template_name = "crm/cliente_lista.html"
    context_object_name = "clientes"
    paginate_by = 25

    def get_queryset(self):
        qs = Cliente.objects.select_related("categoria").prefetch_related("tags")
        p = self.request.GET
        if termo := p.get("q", "").strip():
            qs = qs.filter(
                Q(nome__icontains=termo) | Q(nome_social__icontains=termo)
                | Q(email__icontains=termo) | Q(telefone__icontains=termo)
                | Q(whatsapp__icontains=termo) | Q(curso__icontains=termo)
            )
        if cat := p.get("categoria"):
            qs = qs.filter(categoria_id=cat)
        if rel := p.get("relacionamento"):
            qs = qs.filter(relacionamento=rel)
        if p.get("fgv") == "1":
            qs = qs.filter(membro_fgv=True)
        return qs.order_by("nome")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categorias"] = CategoriaCliente.objects.filter(ativo=True)
        ctx["relacionamentos"] = Cliente.Relacionamento.choices
        ctx["filtros"] = self.request.GET
        return ctx


class ClienteDetailView(PerfilRequeridoMixin, DetailView):
    model = Cliente
    perfis_permitidos = LEITURA
    template_name = "crm/cliente_detalhe.html"
    context_object_name = "cliente"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["interacoes"] = self.object.interacoes.select_related("registrado_por")
        ctx["pedidos"] = self.object.pedidos.order_by("-criado_em")[:20]
        ctx["form_interacao"] = InteracaoForm()
        return ctx


class ClienteCreateView(EscritaPerfilMixin, CreateView):
    model = Cliente
    perfis_permitidos = ESCRITA
    form_class = ClienteForm
    template_name = "crm/cliente_form.html"

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        resp = super().form_valid(form)
        registrar_atividade(
            self.request.user, "cadastrou cliente", self.object.nome,
            url=self.object.get_absolute_url(),
        )
        messages.success(self.request, "Cliente cadastrado.")
        return resp


class ClienteUpdateView(EscritaPerfilMixin, UpdateView):
    model = Cliente
    perfis_permitidos = ESCRITA
    form_class = ClienteForm
    template_name = "crm/cliente_form.html"

    def form_valid(self, form):
        resp = super().form_valid(form)
        registrar_atividade(
            self.request.user, "editou cliente", self.object.nome,
            url=self.object.get_absolute_url(),
        )
        messages.success(self.request, "Cliente atualizado.")
        return resp


class ClienteDeleteView(EscritaPerfilMixin, DeleteView):
    model = Cliente
    perfis_permitidos = [PERFIL_ADMIN]
    template_name = "confirmar_exclusao.html"
    success_url = reverse_lazy("crm:cliente_lista")

    def form_valid(self, form):
        registrar_atividade(self.request.user, "excluiu cliente", self.object.nome)
        messages.success(self.request, "Cliente excluído.")
        return super().form_valid(form)


class InteracaoCreateView(EscritaPerfilMixin, CreateView):
    model = Interacao
    perfis_permitidos = ESCRITA
    form_class = InteracaoForm

    def form_valid(self, form):
        form.instance.cliente = get_object_or_404(Cliente, pk=self.kwargs["pk"])
        form.instance.registrado_por = self.request.user
        form.save()
        messages.success(self.request, "Interação registrada.")
        return redirect("crm:cliente_detalhe", pk=self.kwargs["pk"])

    def form_invalid(self, form):
        messages.error(self.request, "Não foi possível registrar a interação.")
        return redirect("crm:cliente_detalhe", pk=self.kwargs["pk"])


def exportar_clientes(request):
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = 'attachment; filename="clientes.csv"'
    w = csv.writer(resp)
    w.writerow(["nome", "email", "telefone", "whatsapp", "curso", "periodo",
                "campus", "cidade", "categoria", "relacionamento", "origem"])
    for c in Cliente.objects.select_related("categoria"):
        w.writerow([c.nome, c.email, c.telefone, c.whatsapp, c.curso, c.periodo,
                    c.campus, c.cidade,
                    c.categoria.nome if c.categoria else "",
                    c.get_relacionamento_display(), c.origem])
    return resp


def importar_clientes(request):
    if not request.user.is_authenticated or request.user.somente_leitura:
        messages.error(request, "Sem permissão para importar.")
        return redirect("crm:cliente_lista")

    form = ImportarClientesForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        arquivo = form.cleaned_data["arquivo"]
        try:
            linhas = arquivo.read().decode("utf-8-sig").splitlines()
        except UnicodeDecodeError:
            linhas = arquivo.read().decode("latin-1").splitlines()
        leitor = csv.DictReader(linhas)
        criados = 0
        for row in leitor:
            nome = (row.get("nome") or "").strip()
            if not nome:
                continue
            cat = None
            if row.get("categoria"):
                cat, _ = CategoriaCliente.objects.get_or_create(
                    nome=row["categoria"].strip()
                )
            Cliente.objects.create(
                nome=nome,
                email=(row.get("email") or "").strip(),
                telefone=(row.get("telefone") or "").strip(),
                whatsapp=(row.get("whatsapp") or "").strip(),
                curso=(row.get("curso") or "").strip(),
                periodo=(row.get("periodo") or "").strip(),
                campus=(row.get("campus") or "").strip(),
                cidade=(row.get("cidade") or "").strip(),
                origem=(row.get("origem") or "").strip(),
                observacoes=(row.get("observacoes") or "").strip(),
                categoria=cat,
                criado_por=request.user,
            )
            criados += 1
        registrar_atividade(request.user, "importou clientes", f"{criados} registros")
        messages.success(request, f"{criados} cliente(s) importado(s).")
        return redirect("crm:cliente_lista")

    from django.shortcuts import render

    return render(request, "crm/cliente_importar.html", {"form": form})
