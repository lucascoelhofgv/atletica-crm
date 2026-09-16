"""Mixins de controle de acesso por perfil.

Uso:

    class ClienteList(PerfilRequeridoMixin, ListView):
        perfis_permitidos = [PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_OPERACIONAL]

O superusuário e o perfil Administrador sempre passam. Views de escrita devem
usar ``EscritaPerfilMixin`` para bloquear o perfil Visualização.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

from apps.contas.models import PERFIL_ADMIN


class PerfilRequeridoMixin(LoginRequiredMixin):
    perfis_permitidos: list[str] | None = None
    #: quando True, o perfil "Visualização" nunca acessa (telas de escrita)
    bloqueia_visualizacao = False

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        if user.is_superuser or PERFIL_ADMIN in user.perfis:
            return super().dispatch(request, *args, **kwargs)

        if self.bloqueia_visualizacao and user.somente_leitura:
            raise PermissionDenied(
                "Seu perfil tem acesso somente de leitura."
            )

        if self.perfis_permitidos is None:
            return super().dispatch(request, *args, **kwargs)

        if set(self.perfis_permitidos) & set(user.perfis):
            return super().dispatch(request, *args, **kwargs)

        raise PermissionDenied(
            "Você não tem permissão para acessar esta área."
        )


class EscritaPerfilMixin(PerfilRequeridoMixin):
    bloqueia_visualizacao = True


# --------------------------------------------------------------------------- #
# Tabela única de perfis por módulo (usada pelas views de template e pela API)
# --------------------------------------------------------------------------- #
from apps.contas.models import (  # noqa: E402
    PERFIL_DIRETORIA, PERFIL_ESTOQUE, PERFIL_OPERACIONAL, PERFIS,
)

TODOS_PERFIS = list(PERFIS)

#: ``None`` em leitura/escrita significa "qualquer usuário logado".
#: ``excluir`` é quem pode apagar registros (superusuário/Administrador
#: sempre passam em tudo).
PERFIS_MODULO = {
    "crm": {
        "leitura": TODOS_PERFIS,
        "escrita": [PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_OPERACIONAL],
        "excluir": [PERFIL_ADMIN],
    },
    "catalogo": {
        "leitura": TODOS_PERFIS,
        "escrita": [PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_ESTOQUE],
        "excluir": [PERFIL_ADMIN],
    },
    "vendas": {
        "leitura": TODOS_PERFIS,
        "escrita": [PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_OPERACIONAL],
        "excluir": [PERFIL_ADMIN],
    },
    "fornecedores": {
        "leitura": TODOS_PERFIS,
        "escrita": [PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_ESTOQUE],
        "excluir": [PERFIL_ADMIN],
    },
    "eventos": {
        "leitura": TODOS_PERFIS,
        "escrita": [PERFIL_ADMIN, PERFIL_DIRETORIA, PERFIL_OPERACIONAL],
        "excluir": [PERFIL_ADMIN],
    },
    "tarefas": {"leitura": None, "escrita": None, "excluir": None},
    "relatorios": {"leitura": None, "escrita": [PERFIL_ADMIN], "excluir": [PERFIL_ADMIN]},
    "membros": {
        "leitura": [PERFIL_ADMIN, PERFIL_DIRETORIA],
        "escrita": [PERFIL_ADMIN],
        "excluir": [PERFIL_ADMIN],
    },
    "administracao": {  # identidade visual, Sheets, importação
        "leitura": [PERFIL_ADMIN],
        "escrita": [PERFIL_ADMIN],
        "excluir": [PERFIL_ADMIN],
    },
}


def _tem_algum(user, perfis):
    if perfis is None:
        return True
    return bool(set(perfis) & set(user.perfis))


def pode_ler(user, modulo):
    if not getattr(user, "is_authenticated", False):
        return False
    if user.eh_admin:
        return True
    regras = PERFIS_MODULO.get(modulo)
    if regras is None:
        return True
    return _tem_algum(user, regras["leitura"])


def pode_escrever(user, modulo):
    if not getattr(user, "is_authenticated", False):
        return False
    if user.eh_admin:
        return True
    if user.somente_leitura:
        return False
    regras = PERFIS_MODULO.get(modulo)
    if regras is None:
        return True
    return _tem_algum(user, regras["escrita"])


def pode_excluir(user, modulo):
    if not pode_escrever(user, modulo):
        return False
    if user.eh_admin:
        return True
    regras = PERFIS_MODULO.get(modulo)
    if regras is None:
        return True
    return _tem_algum(user, regras["excluir"])


def mapa_permissoes(user):
    """``{modulo: {"ler", "escrever", "excluir"}}`` para o frontend esconder o
    que o usuário não pode fazer (o backend continua sendo a barreira real)."""
    return {
        modulo: {
            "ler": pode_ler(user, modulo),
            "escrever": pode_escrever(user, modulo),
            "excluir": pode_excluir(user, modulo),
        }
        for modulo in PERFIS_MODULO
    }
