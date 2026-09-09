"""Modelo de usuário do CRM: o Membro da Atlética.

Os *perfis de acesso* (Administrador, Diretoria, Operacional, Estoque,
Financeiro, Visualização) são representados por Grupos do Django, criados pelo
comando ``seed_inicial``. Assim é possível criar novos perfis no futuro sem
alterar o código.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from simple_history.models import HistoricalRecords

# Nomes canônicos dos perfis. Referenciados em mixins de permissão e no seed.
PERFIL_ADMIN = "Administrador"
PERFIL_DIRETORIA = "Diretoria"
PERFIL_OPERACIONAL = "Operacional"
PERFIL_ESTOQUE = "Estoque"
PERFIL_FINANCEIRO = "Financeiro"
PERFIL_VISUALIZACAO = "Visualização"

PERFIS = [
    PERFIL_ADMIN,
    PERFIL_DIRETORIA,
    PERFIL_OPERACIONAL,
    PERFIL_ESTOQUE,
    PERFIL_FINANCEIRO,
    PERFIL_VISUALIZACAO,
]


class Membro(AbstractUser):
    """Usuário do sistema. Um membro que sai da Atlética é *desativado*
    (``is_active = False``), preservando todo o histórico que ele criou."""

    email = models.EmailField("e-mail", unique=True)
    cargo = models.CharField(
        "cargo ou função na Atlética", max_length=120, blank=True
    )
    telefone = models.CharField("telefone", max_length=40, blank=True)
    foto = models.ImageField(
        "foto", upload_to="membros/", blank=True, null=True
    )
    data_entrada = models.DateField("data de entrada", null=True, blank=True)
    data_saida = models.DateField("data de saída", null=True, blank=True)
    observacoes = models.TextField("observações", blank=True)

    history = HistoricalRecords()

    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = "membro"
        verbose_name_plural = "membros"
        ordering = ["first_name", "last_name", "username"]

    def __str__(self):
        nome = self.get_full_name()
        return nome or self.username

    @property
    def nome_exibicao(self):
        return self.get_full_name() or self.username

    @property
    def perfis(self):
        return list(self.groups.values_list("name", flat=True))

    @property
    def perfil_principal(self):
        ordem = {p: i for i, p in enumerate(PERFIS)}
        atuais = sorted(self.perfis, key=lambda p: ordem.get(p, 99))
        return atuais[0] if atuais else "Sem perfil"

    def tem_perfil(self, *nomes):
        return self.is_superuser or bool(set(nomes) & set(self.perfis))

    @property
    def eh_admin(self):
        return self.is_superuser or PERFIL_ADMIN in self.perfis

    @property
    def somente_leitura(self):
        """True quando o único perfil do membro é Visualização."""
        p = set(self.perfis)
        return p == {PERFIL_VISUALIZACAO} and not self.is_superuser
