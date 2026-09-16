import pytest

from apps.contas.models import PERFIL_VISUALIZACAO
from apps.nucleo.models import LogAcesso

pytestmark = pytest.mark.django_db


def test_saude_publica(api):
    r = api.get("/api/saude/")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_rota_inexistente_devolve_404_json(api):
    r = api.get("/api/nao-existe/")
    assert r.status_code == 404
    assert r.json()["erro"]["codigo"] == "nao_encontrado"


def test_me_sem_sessao_devolve_401(api):
    r = api.get("/api/auth/me/")
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "nao_autenticado"
    assert "csrftoken" in r.cookies


def test_config_e_publica(api):
    r = api.get("/api/config/")
    assert r.status_code == 200
    assert r.json()["cor_primaria"].startswith("#")


def test_config_patch_exige_admin(api, criar_membro):
    api.force_login(criar_membro(PERFIL_VISUALIZACAO))
    r = api.patch("/api/config/", {"titulo_app": "X"}, format="json")
    assert r.status_code == 403
    assert r.json()["erro"]["codigo"] == "permissao_negada"


def test_login_ok_grava_acesso(api, admin):
    r = api.post("/api/auth/login/", {"usuario": "admin", "senha": "senha-forte-123"},
                 format="json")
    assert r.status_code == 200, r.content
    corpo = r.json()
    assert corpo["username"] == "admin"
    assert corpo["eh_admin"] is True
    assert corpo["permissoes"]["crm"]["escrever"] is True
    assert LogAcesso.objects.filter(usuario=admin, sucesso=True).exists()

    r = api.get("/api/auth/me/")
    assert r.status_code == 200


def test_login_por_email(api, admin):
    r = api.post("/api/auth/login/",
                 {"usuario": "ADMIN@atletica.test", "senha": "senha-forte-123"},
                 format="json")
    assert r.status_code == 200


def test_login_senha_errada(api, admin):
    r = api.post("/api/auth/login/", {"usuario": "admin", "senha": "errada"},
                 format="json")
    assert r.status_code == 400
    assert "inválidos" in r.json()["erro"]["mensagem"]
    assert LogAcesso.objects.filter(usuario=admin, sucesso=False).exists()


def test_login_usuario_inativo(api, criar_membro):
    criar_membro(username="saiu", is_active=False)
    r = api.post("/api/auth/login/", {"usuario": "saiu", "senha": "senha-forte-123"},
                 format="json")
    assert r.status_code == 400


def test_logout(api_admin):
    r = api_admin.post("/api/auth/logout/")
    assert r.status_code == 204
    assert api_admin.get("/api/auth/me/").status_code == 401


def test_login_exige_csrf(api_csrf, admin):
    sem_token = api_csrf.post("/api/auth/login/",
                              {"usuario": "admin", "senha": "senha-forte-123"},
                              format="json")
    assert sem_token.status_code == 403

    api_csrf.get("/api/auth/csrf/")
    token = api_csrf.cookies["csrftoken"].value
    com_token = api_csrf.post("/api/auth/login/",
                              {"usuario": "admin", "senha": "senha-forte-123"},
                              format="json", HTTP_X_CSRFTOKEN=token)
    assert com_token.status_code == 200


def test_mutacao_logada_exige_csrf(api_csrf, admin):
    api_csrf.force_login(admin)
    r = api_csrf.post("/api/auth/logout/")
    assert r.status_code == 403
    assert r.json()["erro"]["codigo"] == "permissao_negada"


def test_alterar_senha(api_admin, admin):
    r = api_admin.post("/api/auth/senha/", {
        "senha_atual": "errada", "senha_nova": "nova-senha-forte-456",
        "senha_nova_confirmacao": "nova-senha-forte-456",
    }, format="json")
    assert r.status_code == 400
    assert "senha_atual" in r.json()["erro"]["campos"]

    r = api_admin.post("/api/auth/senha/", {
        "senha_atual": "senha-forte-123", "senha_nova": "nova-senha-forte-456",
        "senha_nova_confirmacao": "nova-senha-forte-456",
    }, format="json")
    assert r.status_code == 200
    admin.refresh_from_db()
    assert admin.check_password("nova-senha-forte-456")
    # sessão continua válida depois da troca
    assert api_admin.get("/api/auth/me/").status_code == 200


def test_atividades_e_acessos_paginados(api_admin):
    r = api_admin.get("/api/atividades/")
    assert r.status_code == 200
    assert set(r.json()) == {"total", "pagina", "paginas", "resultados"}
    r = api_admin.get("/api/acessos/?tamanho=5")
    assert r.status_code == 200
