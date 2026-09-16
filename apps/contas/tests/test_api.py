import pytest
from django.contrib.auth.models import Group

from apps.contas.models import PERFIL_DIRETORIA, PERFIL_ESTOQUE, PERFIL_OPERACIONAL, Membro
from apps.crm.models import Cliente

pytestmark = pytest.mark.django_db


def test_lista_e_opcoes(api_admin, criar_membro, perfis):
    criar_membro(PERFIL_ESTOQUE, username="joao", first_name="João")
    d = api_admin.get("/api/membros/").json()
    assert d["total"] == 2
    joao = next(m for m in d["resultados"] if m["username"] == "joao")
    assert joao["perfis"] == ["Estoque"] and joao["perfil_principal"] == "Estoque"
    assert api_admin.get("/api/membros/?q=joão").json()["total"] == 1
    o = api_admin.get("/api/membros/opcoes/").json()
    assert len(o["grupos"]) == 6 and o["perfis_ordem"][0] == "Administrador"


def test_criar_editar_alternar(api_admin, admin, perfis):
    g = Group.objects.get(name=PERFIL_OPERACIONAL).id
    r = api_admin.post("/api/membros/", {"username": "maria", "first_name": "Maria", "email": "m@x.test",
                                          "senha": "curta"}, format="json")
    assert r.status_code == 400 and "senha" in r.json()["erro"]["campos"]
    r = api_admin.post("/api/membros/", {"username": "maria", "first_name": "Maria", "email": "m@x.test",
                                          "senha": "Senha-forte-2026", "grupos_ids": [g], "cargo": "Tesoureira"}, format="json")
    assert r.status_code == 201, r.content
    mid = r.json()["id"]
    assert r.json()["perfis"] == ["Operacional"]
    assert Membro.objects.get(pk=mid).check_password("Senha-forte-2026")

    r = api_admin.patch(f"/api/membros/{mid}/", {"cargo": "Diretora", "grupos_ids": []}, format="json")
    assert r.status_code == 200 and r.json()["cargo"] == "Diretora" and r.json()["perfis"] == []

    r = api_admin.post(f"/api/membros/{mid}/alternar/")
    assert r.status_code == 200 and r.json()["is_active"] is False and r.json()["data_saida"]
    assert api_admin.post(f"/api/membros/{mid}/alternar/").json()["is_active"] is True
    assert api_admin.post(f"/api/membros/{admin.id}/alternar/").status_code == 400
    assert api_admin.delete(f"/api/membros/{mid}/").status_code == 405


def test_permissoes(api, criar_membro, perfis):
    api.force_login(criar_membro(PERFIL_DIRETORIA))
    assert api.get("/api/membros/").status_code == 200
    assert api.post("/api/membros/", {"username": "x", "senha": "Senha-forte-2026"}, format="json").status_code == 403
    api.force_login(criar_membro(PERFIL_ESTOQUE))
    assert api.get("/api/membros/").status_code == 403


def test_meus_dados(api_admin, admin):
    r = api_admin.patch("/api/auth/me/", {"first_name": "Cadu", "telefone": "21 9"}, format="json")
    assert r.status_code == 200 and r.json()["nome"].startswith("Cadu")
    admin.refresh_from_db()
    assert admin.first_name == "Cadu"
    assert api_admin.patch("/api/auth/me/", {"is_active": False, "cargo": "Presidente", "first_name": "X"}, format="json").status_code == 200
    admin.refresh_from_db()
    assert admin.is_active is True and admin.cargo == ""   # campos fora do "meus dados" são ignorados


def test_busca_global(api_admin, api, criar_membro, perfis):
    Cliente.objects.create(nome="Ana Prado", email="ana@x.test")
    d = api_admin.get("/api/busca/?q=ana").json()
    grupos = {g["grupo"]: g for g in d["grupos"]}
    assert grupos["clientes"]["itens"][0]["url"] == f"/clientes/{Cliente.objects.get().id}"
    assert api_admin.get("/api/busca/?q=a").json()["grupos"] == []
    api.force_login(criar_membro(PERFIL_ESTOQUE))
    assert "membros" not in {g["grupo"] for g in api.get("/api/busca/?q=ana").json()["grupos"]}
