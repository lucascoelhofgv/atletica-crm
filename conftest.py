"""Fixtures compartilhadas dos testes (pytest-django)."""

import itertools

import pytest
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from apps.contas.models import PERFIL_ADMIN, PERFIS, Membro

_seq = itertools.count(1)


@pytest.fixture
def criar_membro(db):
    """``criar_membro("Estoque")`` cria um membro com esse perfil (Group).
    ``criar_membro(None)`` cria sem perfil; ``superuser=True`` marca superusuário."""

    def _criar(perfil=PERFIL_ADMIN, senha="senha-forte-123", superuser=False, **extra):
        n = next(_seq)
        membro = Membro.objects.create_user(
            username=extra.pop("username", f"membro{n}"),
            email=extra.pop("email", f"membro{n}@atletica.test"),
            password=senha,
            first_name=extra.pop("first_name", f"Membro {n}"),
            is_superuser=superuser,
            is_staff=superuser,
            **extra,
        )
        if perfil:
            grupo, _ = Group.objects.get_or_create(name=perfil)
            membro.groups.add(grupo)
        return membro

    return _criar


@pytest.fixture
def perfis(db):
    for nome in PERFIS:
        Group.objects.get_or_create(name=nome)


@pytest.fixture
def admin(criar_membro):
    return criar_membro(PERFIL_ADMIN, username="admin", email="admin@atletica.test")


@pytest.fixture
def api():
    """Cliente anônimo (sem checagem de CSRF, como o padrão do DRF em testes)."""
    return APIClient()


@pytest.fixture
def api_admin(api, admin):
    api.force_login(admin)
    return api


@pytest.fixture
def api_csrf():
    """Cliente que EXIGE CSRF, para testar a proteção de verdade."""
    return APIClient(enforce_csrf_checks=True)
