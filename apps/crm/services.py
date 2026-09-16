"""Lógica de clientes compartilhada pela tela antiga e pela API."""

from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce

from apps.nucleo.models import registrar_atividade
from apps.relatorios.services import csv_response

from .models import Cliente

STATUS_RECEITA = ["pago", "em_separacao", "pronto", "entregue"]
STATUS_IGNORADOS = ["rascunho", "cancelado"]
DEC = DecimalField(max_digits=12, decimal_places=2)


def buscar(qs, termo: str):
    termo = (termo or "").strip()
    if not termo:
        return qs
    return qs.filter(
        Q(nome__icontains=termo) | Q(nome_social__icontains=termo)
        | Q(email__icontains=termo) | Q(telefone__icontains=termo)
        | Q(whatsapp__icontains=termo) | Q(curso__icontains=termo)
    )


def com_totais(qs):
    """Anota nº de pedidos válidos e total gasto (pedidos com receita)."""
    from django.db.models import Count

    return qs.annotate(
        qtd_pedidos=Count("pedidos", filter=~Q(pedidos__status__in=STATUS_IGNORADOS), distinct=True),
        total_gasto_calc=Coalesce(
            Sum("pedidos__valor_total", filter=Q(pedidos__status__in=STATUS_RECEITA)),
            Value(0), output_field=DEC,
        ),
    )


def url_spa(cliente: Cliente) -> str:
    return f"/clientes/{cliente.pk}"


def registrar(usuario, verbo: str, cliente: Cliente):
    registrar_atividade(usuario, verbo, cliente.nome, url=url_spa(cliente))


def exportar_csv(qs=None):
    qs = qs if qs is not None else Cliente.objects.all()
    qs = qs.select_related("categoria").order_by("nome")
    return csv_response(
        "clientes",
        ["nome", "email", "telefone", "whatsapp", "curso", "periodo", "campus", "cidade",
         "categoria", "relacionamento", "origem", "aceita_comunicacoes"],
        [[c.nome, c.email, c.telefone, c.whatsapp, c.curso, c.periodo, c.campus, c.cidade,
          c.categoria.nome if c.categoria else "", c.get_relacionamento_display(), c.origem,
          "sim" if c.aceita_comunicacoes else "não"] for c in qs],
    )
