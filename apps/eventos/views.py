from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from apps.contas.models import (
    PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_FINANCEIRO, PERFIL_OPERACIONAL,
)
from apps.nucleo.models import registrar_atividade
from apps.nucleo.permissoes import EscritaPerfilMixin, PerfilRequeridoMixin

from .forms import CustoForm, EventoForm, LoteForm, ReceitaForm
from .models import CustoEvento, Evento, LoteIngresso, ReceitaEvento

LEITURA = [PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_OPERACIONAL, PERFIL_FINANCEIRO,
           "Estoque", "Visualização"]
ESCRITA = [PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_OPERACIONAL]


def _pode_escrever(user):
    return user.is_superuser or bool(set(ESCRITA) & set(user.perfis))


class EventoListView(PerfilRequeridoMixin, ListView):
    perfis_permitidos = LEITURA
    template_name = "eventos/lista.html"
    context_object_name = "eventos"
    paginate_by = 30

    def get_queryset(self):
        qs = Evento.objects.select_related("responsavel").prefetch_related(
            "lotes", "custos", "receitas"
        )
        p = self.request.GET
        if termo := p.get("q", "").strip():
            qs = qs.filter(Q(nome__icontains=termo) | Q(local__icontains=termo))
        if tipo := p.get("tipo"):
            qs = qs.filter(tipo=tipo)
        if p.get("apenas_festas") == "1":
            qs = qs.filter(tipo=Evento.Tipo.FESTA)
        if status := p.get("status"):
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tipos"] = Evento.Tipo.choices
        ctx["status_choices"] = Evento.Status.choices
        ctx["filtros"] = self.request.GET
        ctx["pode_escrever"] = _pode_escrever(self.request.user)
        return ctx


class EventoDetailView(PerfilRequeridoMixin, DetailView):
    model = Evento
    perfis_permitidos = LEITURA
    template_name = "eventos/detalhe.html"
    context_object_name = "evento"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["lotes"] = self.object.lotes.all()
        ctx["custos"] = self.object.custos.select_related("fornecedor")
        ctx["receitas"] = self.object.receitas.all()
        ctx["form_lote"] = LoteForm()
        ctx["form_custo"] = CustoForm()
        ctx["form_receita"] = ReceitaForm()
        ctx["pode_escrever"] = _pode_escrever(self.request.user)
        return ctx


class EventoCreateView(EscritaPerfilMixin, CreateView):
    model = Evento
    perfis_permitidos = ESCRITA
    form_class = EventoForm
    template_name = "eventos/form.html"

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        resp = super().form_valid(form)
        registrar_atividade(self.request.user, "criou evento", self.object.nome,
                            url=self.object.get_absolute_url())
        messages.success(self.request, "Evento criado. Agora adicione lotes e custos.")
        return resp


class EventoUpdateView(EscritaPerfilMixin, UpdateView):
    model = Evento
    perfis_permitidos = ESCRITA
    form_class = EventoForm
    template_name = "eventos/form.html"

    def form_valid(self, form):
        resp = super().form_valid(form)
        registrar_atividade(self.request.user, "editou evento", self.object.nome,
                            url=self.object.get_absolute_url())
        messages.success(self.request, "Evento atualizado.")
        return resp


class EventoDeleteView(EscritaPerfilMixin, DeleteView):
    model = Evento
    perfis_permitidos = [PERFIL_ADMIN]
    template_name = "confirmar_exclusao.html"
    success_url = reverse_lazy("eventos:lista")

    def form_valid(self, form):
        registrar_atividade(self.request.user, "excluiu evento", self.object.nome)
        messages.success(self.request, "Evento excluído.")
        return super().form_valid(form)


def _add_linha(request, pk, form_cls, campo_fk="evento"):
    evento = get_object_or_404(Evento, pk=pk)
    if not _pode_escrever(request.user):
        raise PermissionDenied
    if request.method == "POST":
        form = form_cls(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            setattr(obj, campo_fk, evento)
            obj.save()
            messages.success(request, "Adicionado.")
        else:
            messages.error(request, "Confira os campos.")
    return redirect("eventos:detalhe", pk=pk)


def lote_add(request, pk):
    return _add_linha(request, pk, LoteForm)


def custo_add(request, pk):
    return _add_linha(request, pk, CustoForm)


def receita_add(request, pk):
    return _add_linha(request, pk, ReceitaForm)


def _del_linha(request, pk, modelo, obj_id):
    evento = get_object_or_404(Evento, pk=pk)
    if not _pode_escrever(request.user):
        raise PermissionDenied
    if request.method == "POST":
        modelo.objects.filter(pk=obj_id, evento=evento).delete()
        messages.success(request, "Removido.")
    return redirect("eventos:detalhe", pk=pk)


def lote_del(request, pk, lote_id):
    return _del_linha(request, pk, LoteIngresso, lote_id)


def custo_del(request, pk, custo_id):
    return _del_linha(request, pk, CustoEvento, custo_id)


def receita_del(request, pk, receita_id):
    return _del_linha(request, pk, ReceitaEvento, receita_id)


def sincronizar_festas(request):
    if not (request.user.is_authenticated and (
        request.user.is_superuser or PERFIL_ADMIN in request.user.perfis
    )):
        raise PermissionDenied
    if request.method == "POST":
        from apps.nucleo.sheets import SheetsIndisponivel
        from .sheets import exportar_festas

        try:
            n = exportar_festas()
            registrar_atividade(request.user, "sincronizou festas com Sheets",
                                f"{n} evento(s)")
            messages.success(request, f"Aba 'Festas' atualizada com {n} evento(s).")
        except SheetsIndisponivel as exc:
            messages.error(request, f"Integração não configurada: {exc}")
        except Exception as exc:  # pragma: no cover
            messages.error(request, f"Falha: {exc}")
    return redirect("nucleo:sheets")
