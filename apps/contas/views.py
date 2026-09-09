from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from apps.contas.models import PERFIL_ADMIN, PERFIL_DIRETORIA, Membro
from apps.nucleo.models import registrar_atividade
from apps.nucleo.permissoes import EscritaPerfilMixin

from .forms import MembroCreateForm, MembroUpdateForm, MeusDadosForm


class MembroListView(EscritaPerfilMixin, ListView):
    model = Membro
    perfis_permitidos = [PERFIL_ADMIN, PERFIL_DIRETORIA]
    template_name = "contas/membro_lista.html"
    context_object_name = "membros"
    paginate_by = 25

    def get_queryset(self):
        qs = Membro.objects.prefetch_related("groups").order_by(
            "-is_active", "first_name", "username"
        )
        busca = self.request.GET.get("q", "").strip()
        if busca:
            qs = qs.filter(username__icontains=busca) | qs.filter(
                first_name__icontains=busca
            ) | qs.filter(last_name__icontains=busca) | qs.filter(
                email__icontains=busca
            )
        return qs.distinct()


class MembroCreateView(EscritaPerfilMixin, CreateView):
    model = Membro
    perfis_permitidos = [PERFIL_ADMIN]
    form_class = MembroCreateForm
    template_name = "contas/membro_form.html"
    success_url = reverse_lazy("contas:membro_lista")

    def form_valid(self, form):
        resp = super().form_valid(form)
        registrar_atividade(
            self.request.user, "criou membro", self.object.nome_exibicao
        )
        messages.success(self.request, "Membro criado com sucesso.")
        return resp


class MembroUpdateView(EscritaPerfilMixin, UpdateView):
    model = Membro
    perfis_permitidos = [PERFIL_ADMIN]
    form_class = MembroUpdateForm
    template_name = "contas/membro_form.html"
    success_url = reverse_lazy("contas:membro_lista")

    def form_valid(self, form):
        resp = super().form_valid(form)
        registrar_atividade(
            self.request.user, "editou membro", self.object.nome_exibicao
        )
        messages.success(self.request, "Membro atualizado.")
        return resp


def membro_alternar_ativo(request, pk):
    if request.method != "POST":
        return redirect("contas:membro_lista")
    if not (request.user.is_superuser or PERFIL_ADMIN in request.user.perfis):
        messages.error(request, "Apenas administradores podem fazer isso.")
        return redirect("contas:membro_lista")
    membro = get_object_or_404(Membro, pk=pk)
    if membro == request.user:
        messages.error(request, "Você não pode desativar a própria conta.")
        return redirect("contas:membro_lista")
    membro.is_active = not membro.is_active
    from django.utils import timezone

    if not membro.is_active and not membro.data_saida:
        membro.data_saida = timezone.localdate()
    membro.save(update_fields=["is_active", "data_saida"])
    registrar_atividade(
        request.user,
        "desativou membro" if not membro.is_active else "reativou membro",
        membro.nome_exibicao,
    )
    messages.success(
        request,
        f"Acesso de {membro.nome_exibicao} "
        f"{'desativado' if not membro.is_active else 'reativado'}.",
    )
    return redirect("contas:membro_lista")


class MeusDadosView(LoginRequiredMixin, UpdateView):
    form_class = MeusDadosForm
    template_name = "contas/meus_dados.html"
    success_url = reverse_lazy("contas:meus_dados")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Dados atualizados.")
        return super().form_valid(form)
