import pytest
from django.test import Client

pytestmark = pytest.mark.django_db


def test_raiz_e_rotas_do_spa_entregam_o_index(api):
    for rota in ("/", "/clientes", "/pedidos/12", "/administracao/membros", "/login"):
        r = api.get(rota)
        # 200 com o build presente; 503 (texto claro) quando o frontend não foi compilado
        assert r.status_code in (200, 503), rota
        assert r["Content-Type"].startswith("text/"), rota


def test_links_antigos_de_app_redirecionam(api):
    r = api.get("/app/clientes/4?x=1")
    assert r.status_code == 301 and r["Location"] == "/clientes/4?x=1"
    assert api.get("/app").status_code == 301


def test_rotas_que_continuam_no_django(api, admin):
    assert api.get("/conta/senha/").status_code == 200
    assert api.get("/admin/login/").status_code == 200
    r = api.get("/pedidos/1/recibo/")
    assert r.status_code == 302 and r["Location"].startswith("/login")
    c = Client()
    c.force_login(admin)
    assert c.get("/pedidos/999/recibo/").status_code == 404
