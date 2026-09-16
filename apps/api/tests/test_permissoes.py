import pytest

from apps.contas.models import (
    PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_ESTOQUE, PERFIL_FINANCEIRO,
    PERFIL_OPERACIONAL, PERFIL_VISUALIZACAO,
)
from apps.nucleo.permissoes import (
    PERFIS_MODULO, mapa_permissoes, pode_escrever, pode_excluir, pode_ler,
)

pytestmark = pytest.mark.django_db

PERFIS_NAO_ADMIN = [PERFIL_DIRETORIA, PERFIL_OPERACIONAL, PERFIL_ESTOQUE,
                    PERFIL_FINANCEIRO, PERFIL_VISUALIZACAO]


@pytest.mark.parametrize("perfil", PERFIS_NAO_ADMIN)
@pytest.mark.parametrize("modulo", list(PERFIS_MODULO))
def test_tabela_e_o_oraculo(criar_membro, perfil, modulo):
    membro = criar_membro(perfil)
    regras = PERFIS_MODULO[modulo]

    esperado_ler = regras["leitura"] is None or perfil in regras["leitura"]
    assert pode_ler(membro, modulo) is esperado_ler

    if perfil == PERFIL_VISUALIZACAO:
        assert pode_escrever(membro, modulo) is False
        assert pode_excluir(membro, modulo) is False
    else:
        esperado_escrever = regras["escrita"] is None or perfil in regras["escrita"]
        assert pode_escrever(membro, modulo) is esperado_escrever
        esperado_excluir = esperado_escrever and (
            regras["excluir"] is None or perfil in regras["excluir"]
        )
        assert pode_excluir(membro, modulo) is esperado_excluir


def test_admin_e_superuser_passam_em_tudo(criar_membro):
    admin = criar_membro(PERFIL_ADMIN)
    root = criar_membro(None, superuser=True)
    for membro in (admin, root):
        for modulo in PERFIS_MODULO:
            assert pode_ler(membro, modulo) and pode_escrever(membro, modulo)
            assert pode_excluir(membro, modulo)


def test_mapa_permissoes_tem_todos_os_modulos(criar_membro):
    mapa = mapa_permissoes(criar_membro(PERFIL_ESTOQUE))
    assert set(mapa) == set(PERFIS_MODULO)
    assert mapa["catalogo"] == {"ler": True, "escrever": True, "excluir": False}
    assert mapa["crm"]["escrever"] is False
