from datetime import timedelta

import pytest
from django.utils import timezone

from apps.contas.models import PERFIL_VISUALIZACAO
from apps.tarefas.models import Tarefa

pytestmark = pytest.mark.django_db


@pytest.fixture
def base(db, admin, criar_membro):
    outro = criar_membro(username="outro")
    hoje = timezone.localdate()
    a = Tarefa.objects.create(titulo="Conferir estoque", responsavel=admin, criador=admin,
                              prazo=hoje - timedelta(days=1), prioridade="urgente")
    b = Tarefa.objects.create(titulo="Fechar pedido", responsavel=outro, criador=admin,
                              prazo=hoje + timedelta(days=3), status="em_andamento")
    c = Tarefa.objects.create(titulo="Antiga", criador=admin, status="concluida")
    return {"outro": outro, "a": a, "b": b, "c": c}


def test_lista_filtros(api_admin, base):
    assert api_admin.get("/api/tarefas/").json()["total"] == 3
    assert api_admin.get("/api/tarefas/?minhas=true").json()["total"] == 1
    assert api_admin.get("/api/tarefas/?atrasadas=true").json()["resultados"][0]["titulo"] == "Conferir estoque"
    assert api_admin.get("/api/tarefas/?abertas=true").json()["total"] == 2
    assert api_admin.get("/api/tarefas/?status=concluida").json()["total"] == 1
    assert api_admin.get("/api/tarefas/?q=pedido").json()["total"] == 1
    primeira = api_admin.get("/api/tarefas/").json()["resultados"][0]
    assert primeira["atrasada"] is True and primeira["prioridade_rotulo"] == "Urgente"


def test_quadro(api_admin, base):
    q = api_admin.get("/api/tarefas/quadro/?abertas=true").json()
    colunas = {c["status"]: c for c in q["colunas"]}
    assert set(colunas) == {"a_fazer", "em_andamento", "aguardando", "concluida", "cancelada"}
    assert len(colunas["a_fazer"]["tarefas"]) == 1 and len(colunas["em_andamento"]["tarefas"]) == 1
    assert colunas["concluida"]["tarefas"] == []


def test_crud_mover_comentar(api_admin, admin, base):
    r = api_admin.post("/api/tarefas/", {"titulo": " Nova ", "responsavel_id": base["outro"].id,
                                          "prioridade": "alta"}, format="json")
    assert r.status_code == 201, r.content
    d = r.json()
    assert d["titulo"] == "Nova" and d["responsavel"]["id"] == base["outro"].id and d["criador"]["id"] == admin.id
    tid = d["id"]

    r = api_admin.post(f"/api/tarefas/{tid}/mover/", {"status": "concluida"}, format="json")
    assert r.status_code == 200 and r.json()["status"] == "concluida" and r.json()["concluida_em"]
    assert api_admin.post(f"/api/tarefas/{tid}/mover/", {"status": "x"}, format="json").status_code == 400
    r = api_admin.post(f"/api/tarefas/{tid}/mover/", {"status": "a_fazer"}, format="json")
    assert r.json()["concluida_em"] is None

    r = api_admin.post(f"/api/tarefas/{tid}/comentarios/", {"texto": "Falei com o fornecedor"}, format="json")
    assert r.status_code == 201 and r.json()["comentarios"][0]["autor"]["id"] == admin.id
    assert r.json()["qtd_comentarios"] == 1
    cid = r.json()["comentarios"][0]["id"]
    assert api_admin.delete(f"/api/tarefas/{tid}/comentarios/{cid}/").json()["qtd_comentarios"] == 0

    assert api_admin.patch(f"/api/tarefas/{tid}/", {"titulo": ""}, format="json").status_code == 400
    assert api_admin.delete(f"/api/tarefas/{tid}/").status_code == 204


def test_qualquer_logado_escreve(api, criar_membro, base):
    api.force_login(criar_membro(PERFIL_VISUALIZACAO))
    assert api.get("/api/tarefas/").status_code == 200
    # Visualização é somente leitura em tudo, inclusive tarefas
    assert api.post("/api/tarefas/", {"titulo": "X"}, format="json").status_code == 403
    api.force_login(criar_membro(None))   # logado sem perfil: tarefas liberam
    r = api.post("/api/tarefas/", {"titulo": "X"}, format="json")
    assert r.status_code == 201
    assert api.get("/api/tarefas/opcoes/").json()["prioridades"]
