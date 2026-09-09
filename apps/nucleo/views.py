from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, TemplateView, UpdateView

from apps.catalogo.models import Produto
from apps.contas.models import PERFIL_ADMIN, Membro
from apps.crm.models import Cliente
from apps.fornecedores.models import Fornecedor
from apps.tarefas.models import Tarefa
from apps.vendas.models import ItemPedido, Pedido

from .forms import ConfiguracaoForm
from .models import Configuracao, LogAcesso, RegistroAtividade

PERIODOS = {
    "hoje": ("Hoje", 0),
    "7d": ("Últimos 7 dias", 7),
    "30d": ("Últimos 30 dias", 30),
    "semestre": ("Este semestre", None),
    "ano": ("Este ano", None),
}


def _intervalo(chave):
    hoje = timezone.localdate()
    if chave == "hoje":
        return hoje, hoje
    if chave == "7d":
        return hoje - timedelta(days=7), hoje
    if chave == "30d":
        return hoje - timedelta(days=30), hoje
    if chave == "ano":
        return hoje.replace(month=1, day=1), hoje
    if chave == "semestre":
        mes_inicio = 1 if hoje.month <= 6 else 7
        return hoje.replace(month=mes_inicio, day=1), hoje
    return hoje - timedelta(days=30), hoje


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "nucleo/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        periodo = self.request.GET.get("periodo", "30d")
        if periodo not in PERIODOS:
            periodo = "30d"
        inicio, fim = _intervalo(periodo)

        pedidos = Pedido.objects.filter(data_compra__range=(inicio, fim))
        pagos = pedidos.filter(status=Pedido.Status.PAGO)
        dec = DecimalField(max_digits=12, decimal_places=2)

        receita = pedidos.filter(
            status__in=[
                Pedido.Status.PAGO, Pedido.Status.SEPARACAO,
                Pedido.Status.PRONTO, Pedido.Status.ENTREGUE,
            ]
        ).aggregate(t=Coalesce(Sum("valor_total"), Value(0), output_field=dec))["t"]

        top_produtos = (
            ItemPedido.objects.filter(pedido__data_compra__range=(inicio, fim))
            .values("produto__nome")
            .annotate(qtd=Sum("quantidade"))
            .order_by("-qtd")[:5]
        )

        ctx.update(
            periodo=periodo,
            periodos=PERIODOS,
            periodo_label=PERIODOS[periodo][0],
            total_vendas=pedidos.exclude(
                status__in=[Pedido.Status.RASCUNHO, Pedido.Status.CANCELADO]
            ).count(),
            receita=receita,
            pedidos_aguardando=Pedido.objects.filter(
                status=Pedido.Status.AGUARDANDO
            ).count(),
            pedidos_pagos=pagos.count(),
            pedidos_retirada=Pedido.objects.filter(
                status__in=[Pedido.Status.SEPARACAO, Pedido.Status.PRONTO]
            ).count(),
            produtos_baixo=Produto.objects.filter(
                status=Produto.Status.ATIVO,
                quantidade_atual__gt=0,
                quantidade_atual__lte=F("estoque_minimo"),
            ).count(),
            produtos_esgotados=Produto.objects.filter(
                status=Produto.Status.ATIVO, quantidade_atual__lte=0
            ).count(),
            clientes_total=Cliente.objects.count(),
            clientes_novos=Cliente.objects.filter(
                criado_em__date__range=(inicio, fim)
            ).count(),
            tarefas_atrasadas=Tarefa.objects.filter(
                prazo__lt=timezone.localdate()
            ).exclude(
                status__in=[Tarefa.Status.CONCLUIDA, Tarefa.Status.CANCELADA]
            ).count(),
            fornecedores_ativos=Fornecedor.objects.filter(
                status=Fornecedor.Status.ATIVO
            ).count(),
            top_produtos=top_produtos,
            atividades=RegistroAtividade.objects.select_related("usuario")[:12],
            minhas_tarefas=Tarefa.objects.filter(
                responsavel=self.request.user
            ).exclude(
                status__in=[Tarefa.Status.CONCLUIDA, Tarefa.Status.CANCELADA]
            ).order_by("prazo")[:6],
            valor_estoque=Produto.objects.aggregate(
                t=Coalesce(
                    Sum(F("custo_unitario") * F("quantidade_atual"),
                        output_field=dec),
                    Value(0), output_field=dec,
                )
            )["t"],
        )
        return ctx


class ConfiguracaoUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ConfiguracaoForm
    template_name = "nucleo/configuracao.html"
    success_url = reverse_lazy("nucleo:configuracao")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not (
            request.user.is_superuser or PERFIL_ADMIN in request.user.perfis
        ):
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied("Apenas administradores acessam as configurações.")
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return Configuracao.carregar()

    def form_valid(self, form):
        messages.success(self.request, "Identidade visual atualizada.")
        return super().form_valid(form)


class AtividadeListView(LoginRequiredMixin, ListView):
    template_name = "nucleo/atividades.html"
    context_object_name = "atividades"
    paginate_by = 50
    queryset = RegistroAtividade.objects.select_related("usuario")


class LogAcessoListView(LoginRequiredMixin, ListView):
    template_name = "nucleo/acessos.html"
    context_object_name = "acessos"
    paginate_by = 50

    def get_queryset(self):
        qs = LogAcesso.objects.select_related("usuario")
        if not (self.request.user.is_superuser
                or PERFIL_ADMIN in self.request.user.perfis):
            qs = qs.filter(usuario=self.request.user)
        return qs


def sincronizar_sheets(request):
    if not request.user.is_authenticated or not (
        request.user.is_superuser or PERFIL_ADMIN in request.user.perfis
    ):
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied
    if request.method == "POST":
        from .sheets import SheetsIndisponivel, exportar_tudo

        try:
            resumo = exportar_tudo()
            registrar_atividade(request.user, "sincronizou Google Sheets",
                                ", ".join(f"{k}: {v}" for k, v in resumo.items()))
            messages.success(
                request,
                "Planilha atualizada — " + ", ".join(
                    f"{k}: {v}" for k, v in resumo.items()
                ),
            )
        except SheetsIndisponivel as exc:
            messages.error(request, f"Integração não configurada: {exc}")
        except Exception as exc:  # pragma: no cover
            messages.error(request, f"Falha ao sincronizar: {exc}")
    return render(request, "nucleo/sheets.html", {
        "configurado": bool(getattr(settings, "GOOGLE_SHEETS_SPREADSHEET_ID", "")),
    })


def busca_global(request):
    termo = request.GET.get("q", "").strip()
    resultados = {}
    if termo:
        resultados = {
            "clientes": Cliente.objects.filter(
                Q(nome__icontains=termo) | Q(email__icontains=termo)
                | Q(telefone__icontains=termo) | Q(whatsapp__icontains=termo)
            )[:10],
            "produtos": Produto.objects.filter(
                Q(nome__icontains=termo) | Q(codigo_interno__icontains=termo)
                | Q(sku__icontains=termo)
            )[:10],
            "pedidos": Pedido.objects.filter(
                Q(numero__icontains=termo) | Q(cliente__nome__icontains=termo)
            )[:10],
            "fornecedores": Fornecedor.objects.filter(
                Q(nome__icontains=termo) | Q(nome_fantasia__icontains=termo)
            )[:10],
            "tarefas": Tarefa.objects.filter(titulo__icontains=termo)[:10],
            "membros": Membro.objects.filter(
                Q(first_name__icontains=termo) | Q(last_name__icontains=termo)
                | Q(username__icontains=termo)
            )[:10],
        }
    return render(
        request, "nucleo/busca.html", {"termo": termo, "resultados": resultados}
    )
