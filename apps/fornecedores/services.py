"""Lógica de fornecedores compartilhada pela tela antiga e pela API."""

from django.db.models import Avg, Count, F, Q

from apps.nucleo.models import registrar_atividade

from .models import Fornecedor


def buscar(qs, termo: str):
    termo = (termo or "").strip()
    if not termo:
        return qs
    return qs.filter(
        Q(nome__icontains=termo) | Q(nome_fantasia__icontains=termo)
        | Q(contato_nome__icontains=termo) | Q(produtos_servicos__icontains=termo)
    )


def com_totais(qs):
    return qs.annotate(
        qtd_produtos=Count("produtos", distinct=True),
        qtd_avaliacoes=Count("avaliacoes", distinct=True),
        nota_media_calc=Avg(
            (F("avaliacoes__preco") + F("avaliacoes__qualidade") + F("avaliacoes__prazo")
             + F("avaliacoes__atendimento") + F("avaliacoes__confiabilidade")) / 5.0
        ),
    )


def url_spa(f: Fornecedor) -> str:
    return f"/fornecedores/{f.pk}"


def registrar(usuario, verbo: str, f: Fornecedor, descricao: str = ""):
    registrar_atividade(usuario, verbo, str(f), descricao, url=url_spa(f))
