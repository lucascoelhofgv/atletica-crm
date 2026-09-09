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
