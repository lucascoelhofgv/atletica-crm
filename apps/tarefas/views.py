from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from apps.nucleo.models import registrar_atividade

from .forms import ComentarioForm, TarefaForm
from .models import Tarefa


class TarefaListView(LoginRequiredMixin, ListView):
    template_name = "tarefas/lista.html"
    context_object_name = "tarefas"
    paginate_by = 40

    def get_queryset(self):
        qs = Tarefa.objects.select_related("responsavel", "cliente", "pedido")
        p = self.request.GET
        if p.get("minhas") == "1":
            qs = qs.filter(responsavel=self.request.user)
        if p.get("atrasadas") == "1":
            from django.utils import timezone

            qs = qs.filter(prazo__lt=timezone.localdate()).exclude(
                status__in=[Tarefa.Status.CONCLUIDA, Tarefa.Status.CANCELADA]
            )
        if status := p.get("status"):
            qs = qs.filter(status=status)
        if resp := p.get("responsavel"):
            qs = qs.filter(responsavel_id=resp)
        if termo := p.get("q", "").strip():
            qs = qs.filter(Q(titulo__icontains=termo) | Q(descricao__icontains=termo))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = Tarefa.Status.choices
        ctx["filtros"] = self.request.GET
        return ctx


def quadro(request):
    if not request.user.is_authenticated:
        return redirect("contas:login")
    colunas = []
    base = Tarefa.objects.select_related("responsavel")
    for valor, rotulo in Tarefa.Status.choices:
        colunas.append((valor, rotulo, base.filter(status=valor)))
    return render(request, "tarefas/quadro.html", {"colunas": colunas})


class TarefaDetailView(LoginRequiredMixin, DetailView):
    model = Tarefa
    template_name = "tarefas/detalhe.html"
    context_object_name = "tarefa"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["comentarios"] = self.object.comentarios.select_related("autor")
        ctx["form_comentario"] = ComentarioForm()
        return ctx


class TarefaCreateView(LoginRequiredMixin, CreateView):
    model = Tarefa
    form_class = TarefaForm
    template_name = "tarefas/form.html"

    def form_valid(self, form):
        form.instance.criador = self.request.user
        resp = super().form_valid(form)
        registrar_atividade(self.request.user, "criou tarefa", self.object.titulo,
                            url=self.object.get_absolute_url())
        messages.success(self.request, "Tarefa criada.")
        return resp


class TarefaUpdateView(LoginRequiredMixin, UpdateView):
    model = Tarefa
    form_class = TarefaForm
    template_name = "tarefas/form.html"

    def form_valid(self, form):
        messages.success(self.request, "Tarefa atualizada.")
        return super().form_valid(form)


class TarefaDeleteView(LoginRequiredMixin, DeleteView):
    model = Tarefa
    template_name = "confirmar_exclusao.html"
    success_url = reverse_lazy("tarefas:lista")

    def form_valid(self, form):
        messages.success(self.request, "Tarefa excluída.")
        return super().form_valid(form)


def mudar_status(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    if request.method == "POST":
        novo = request.POST.get("status")
        if novo in dict(Tarefa.Status.choices):
            tarefa.status = novo
            tarefa.save()
            registrar_atividade(
                request.user, "moveu tarefa",
                f"{tarefa.titulo} → {tarefa.get_status_display()}",
            )
    destino = request.POST.get("next") or "tarefas:quadro"
    return redirect(destino)


def comentar(request, pk):
    tarefa = get_object_or_404(Tarefa, pk=pk)
    if request.method == "POST":
        form = ComentarioForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.tarefa = tarefa
            c.autor = request.user
            c.save()
            messages.success(request, "Comentário adicionado.")
    return redirect("tarefas:detalhe", pk=pk)
