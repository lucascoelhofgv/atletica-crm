"""Cadastro de fontes de planilha e o comando que as importa.

Nenhum teste aqui fala com o Google: a leitura da planilha é trocada por uma
função que devolve linhas prontas, no mesmo formato que ``ler_aba`` devolve
(lista de dicts + cabeçalho).
"""

import io

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.crm.models import Cliente
from apps.nucleo.models import FontePlanilha

pytestmark = pytest.mark.django_db

LINHAS = [
    {"Nome": "Fulano de Tal", "E-mail": "fulano@atletica.test", "Telefone": "21999998888"},
    {"Nome": "Ciclana Souza", "E-mail": "ciclana@atletica.test", "Telefone": ""},
]
CABECALHO = ["Nome", "E-mail", "Telefone"]


def criar_fonte(**extra):
    dados = dict(
        nome="Padrinhos e Membros",
        planilha="https://docs.google.com/spreadsheets/d/ABC123/edit",
        destino=FontePlanilha.Destino.CLIENTES,
    )
    dados.update(extra)
    return FontePlanilha.objects.create(**dados)


@pytest.fixture
def planilha_falsa(monkeypatch):
    def _ler_aba(planilha, aba=None):
        return LINHAS, CABECALHO

    monkeypatch.setattr("apps.nucleo.services.integracoes.ler_aba", _ler_aba)


def rodar(**opts):
    saida = io.StringIO()
    call_command("importar_planilhas", stdout=saida, stderr=io.StringIO(), **opts)
    return saida.getvalue()


def test_sem_fontes_cadastradas_nao_quebra():
    assert "Nada a fazer" in rodar()


def test_importa_fonte_ativa_e_guarda_o_resultado(planilha_falsa):
    fonte = criar_fonte()

    rodar()

    assert Cliente.objects.filter(nome="Fulano de Tal").exists()
    fonte.refresh_from_db()
    assert fonte.ultima_sincronizacao is not None
    assert "2 criado(s)" in fonte.ultimo_resultado
    assert fonte.ultimo_erro == ""


def test_fonte_desativada_fica_de_fora(planilha_falsa):
    criar_fonte(ativa=False)

    rodar()

    assert not Cliente.objects.exists()


def test_fonte_desativada_roda_quando_pedida_pelo_id(planilha_falsa):
    fonte = criar_fonte(ativa=False)

    rodar(fonte=fonte.pk)

    assert Cliente.objects.filter(nome="Fulano de Tal").exists()


def test_simular_nao_grava_nada(planilha_falsa):
    fonte = criar_fonte()

    saida = rodar(simular=True)

    assert "2 linha(s)" in saida
    assert not Cliente.objects.exists()
    fonte.refresh_from_db()
    assert fonte.ultima_sincronizacao is None


def test_uma_fonte_quebrada_nao_impede_as_outras(monkeypatch):
    boa = criar_fonte(nome="Boa")
    ruim = criar_fonte(
        nome="Ruim", planilha="https://docs.google.com/spreadsheets/d/XYZ999/edit"
    )

    def _ler_aba(planilha, aba=None):
        if "XYZ999" in planilha:
            raise RuntimeError("planilha não compartilhada com a conta de serviço")
        return LINHAS, CABECALHO

    monkeypatch.setattr("apps.nucleo.services.integracoes.ler_aba", _ler_aba)

    with pytest.raises(CommandError):
        rodar()

    # A fonte boa (ordenada antes) foi importada mesmo com a outra falhando.
    assert Cliente.objects.filter(nome="Fulano de Tal").exists()
    boa.refresh_from_db()
    ruim.refresh_from_db()
    assert boa.ultima_sincronizacao is not None
    assert "não compartilhada" in ruim.ultimo_erro
    assert ruim.ultima_sincronizacao is None
