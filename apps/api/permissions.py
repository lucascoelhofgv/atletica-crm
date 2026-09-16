"""Permission classes do DRF, espelhando ``PerfilRequeridoMixin`` e
``EscritaPerfilMixin`` das views de template.

Uso num ViewSet::

    class ClienteViewSet(ModelViewSet):
        modulo = "crm"
        permission_classes = [IsAuthenticated, PerfilModulo]
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.nucleo.permissoes import pode_escrever, pode_excluir, pode_ler


class PerfilModulo(BasePermission):
    message = "Você não tem permissão para acessar esta área."

    def has_permission(self, request, view):
        modulo = getattr(view, "modulo", None)
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return pode_ler(user, modulo)
        if user.somente_leitura:
            self.message = "Seu perfil tem acesso somente de leitura."
            return False
        if request.method == "DELETE":
            if not pode_excluir(user, modulo):
                self.message = "Apenas administradores podem excluir registros."
                return False
            return True
        return pode_escrever(user, modulo)


class SomenteAdmin(BasePermission):
    message = "Apenas administradores acessam esta área."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.eh_admin)
