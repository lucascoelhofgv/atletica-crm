"""Gravação das planilhas de Esportes, resumo e API (inclui o botão das fontes).

Nenhum teste fala com o Google: ``ler_grade`` e ``ler_abas`` são trocadas por
funções que devolvem as grades falsas de ``planilhas.py``.
"""

from datetime import date
from decimal import Decimal

import pytest

from apps.contas.models import PERFIL_DIRETORIA, PERFIL_OPERACIONAL
from apps.esportes import services
from apps.esportes.models import Modalidade, OrcamentoModalidade, Sessao
from apps.nucleo.models import FontePlanilha

from . import planilhas

pytestmark = pytest.mark.django_db


@pytest.fixture
def planilhas_falsas(monkeypatch):
    estado = {"treinos": planilhas.treinos(), "orcamento": planilhas.orcamento()}
    monkeypatch.setattr("apps.nucleo.services.integracoes.ler_grade",
                        lambda planilha, aba=None: estado["orcamento"])
    monkeypatch.setattr("apps.nucleo.services.integracoes.ler_abas",
                        lambda planilha: estado["treinos"])
    return estado


def fonte(destino, **extra):
    return FontePlanilha.objects.create(
        nome=extra.pop("nome", destino),
        planilha="https://docs.google.com/spreadsheets/d/XLSX123/edit",
        destino=destino, **extra,
    )


# --------------------------------------------------------------------------- #
# Gravação
# --------------------------------------------------------------------------- #
def test_orcamento_grava_modalidades_e_semestres():
    r = services.importar_orcamento(planilhas.orcamento())

    assert (r["modalidades"], r["criados"], r["atualizados"]) == (4, 8, 0)
    basquete = Modalidade.objects.get(esporte="Basquete", naipe="fem")
    assert basquete.local == "Hebraica" and basquete.nome == "Basquete Feminino"
    orc = OrcamentoModalidade.objects.get(modalidade=basquete, ano=2026, semestre=1)
    # A mesma conta da planilha: 24 x (350 + 125) + 3 x 160 = 11.880
    assert orc.total_previsto == Decimal("11880")


def test_orcamento_de_novo_atualiza_sem_duplicar():
    services.importar_orcamento(planilhas.orcamento())
    r = services.importar_orcamento(planilhas.orcamento())

    assert (r["criados"], r["atualizados"], r["removidos"]) == (0, 8, 0)
    assert OrcamentoModalidade.objects.count() == 8


def test_treinos_gravam_e_sincronizar_de_novo_nao_duplica():
    services.importar_treinos(planilhas.treinos())
    r = services.importar_treinos(planilhas.treinos())

    assert (r["criados"], r["atualizados"], r["removidos"]) == (0, 8, 0)
    assert Sessao.objects.count() == 8
    assert len(r["avisos"]) == 3


def test_linha_apagada_da_planilha_sai_do_crm_so_no_mesmo_semestre():
    services.importar_treinos(planilhas.treinos())
    # Uma sessão de outro semestre que esta planilha não cobre.
    futsal_fem = Modalidade.objects.get(esporte="Futsal", naipe="fem")
    Sessao.objects.create(modalidade=futsal_fem, data=date(2026, 9, 1), custo=Decimal("10"))

    grades = planilhas.treinos()
    grades["FUTSAL"][9][1:6] = [""] * 5  # some o treino de 23/02 (B10:F10)
    r = services.importar_treinos({"FUTSAL": grades["FUTSAL"]})

    assert r["removidos"] == 1
    assert not Sessao.objects.filter(data=date(2026, 2, 23)).exists()
    assert Sessao.objects.filter(data=date(2026, 9, 1)).exists()      # outro semestre
    assert Sessao.objects.filter(modalidade__esporte="Handebol").count() == 2  # outra aba


def test_planilha_sem_treino_nenhum_e_erro():
    with pytest.raises(ValueError, match="Não achei nenhum treino"):
        services.importar_treinos({"X": [["nada"]]})


# --------------------------------------------------------------------------- #
# Resumo
# --------------------------------------------------------------------------- #
def test_resumo_compara_orcado_com_realizado():
    services.importar_orcamento(planilhas.orcamento())
    services.importar_treinos(planilhas.treinos())

    r = services.resumo(2026, 1)
    futsal_masc = next(m for m in r["modalidades"] if m["nome"] == "Futsal Masculino")

    # 24 x (200 + 100) + 4 x 150
    assert futsal_masc["orcado"] == Decimal("7800")
    # treino 24/02 (130 + 140) + treino cancelado 26/02 (0) + 2 jogos (125 cada)
    assert futsal_masc["realizado"] == Decimal("520")
    assert (futsal_masc["treinos_registrados"], futsal_masc["treinos_cancelados"]) == (2, 1)
    assert futsal_masc["jogos_registrados"] == 2
    assert futsal_masc["valor_quadra_orcado"] == Decimal("200")
    assert futsal_masc["valor_quadra_real"] == Decimal("140")

    bateria = next(m for m in r["modalidades"] if m["nome"] == "Bateria")
    assert bateria["tem_orcamento"] and not bateria["tem_registros"]

    fev = next(m for m in r["por_mes"] if m["mes"] == "2026-02")
    assert fev["realizado"] == Decimal("400") and fev["treinos"] == 2
    assert [m["mes"] for m in r["por_mes"]][0] == "2026-01"
    assert r["totais"]["realizado"] == sum(m["realizado"] for m in r["modalidades"])


def test_resumo_sem_semestre_escolhe_o_ultimo_com_treino():
    services.importar_orcamento(planilhas.orcamento())
    services.importar_treinos(planilhas.treinos())  # tem treino em agosto (2º semestre)

    r = services.resumo()

    assert (r["ano"], r["semestre"]) == (2026, 2)
    assert {"ano": 2026, "semestre": 1} in r["semestres_disponiveis"]


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
def test_resumo_e_sessoes_na_api(api, criar_membro):
    services.importar_orcamento(planilhas.orcamento())
    services.importar_treinos(planilhas.treinos())
    api.force_login(criar_membro(PERFIL_OPERACIONAL))

    r = api.get("/api/esportes/resumo/?ano=2026&semestre=1")
    assert r.status_code == 200, r.content
    assert r.json()["totais"]["orcado"] > 0

    r = api.get("/api/esportes/sessoes/?ano=2026&semestre=1&esporte=Futsal")
    assert r.status_code == 200
    assert r.json()["total"] == 6


def test_sessoes_sao_so_leitura(api_admin):
    assert api_admin.post("/api/esportes/sessoes/", {}, format="json").status_code == 405


def test_esportes_aparece_nas_permissoes(api, criar_membro):
    api.force_login(criar_membro(PERFIL_DIRETORIA))

    permissoes = api.get("/api/auth/me/").json()["permissoes"]

    assert permissoes["esportes"] == {"ler": True, "escrever": True, "excluir": False}


def test_botao_sincronizar_roda_a_fonte_e_guarda_o_resultado(api_admin, planilhas_falsas):
    f = fonte(FontePlanilha.Destino.ESPORTES_TREINOS)

    r = api_admin.post(f"/api/integracoes/fontes/{f.pk}/sincronizar/")

    assert r.status_code == 200, r.content
    assert "8 novo(s)" in r.json()["resumo"] and "3 aviso(s)" in r.json()["resumo"]
    assert len(r.json()["avisos"]) == 3
    assert r.json()["fonte"]["ultima_sincronizacao"]
    assert Sessao.objects.count() == 8


def test_simular_nao_grava(api_admin, planilhas_falsas):
    f = fonte(FontePlanilha.Destino.ESPORTES_ORCAMENTO)

    r = api_admin.post(f"/api/integracoes/fontes/{f.pk}/simular/")

    assert r.status_code == 200 and "4 modalidade(s)" in r.json()["resumo"]
    assert not Modalidade.objects.exists()
    f.refresh_from_db()
    assert f.ultima_sincronizacao is None


def test_erro_na_sincronizacao_fica_guardado_na_fonte(api_admin, planilhas_falsas):
    planilhas_falsas["treinos"] = {"X": [["nada"]]}
    f = fonte(FontePlanilha.Destino.ESPORTES_TREINOS)

    r = api_admin.post(f"/api/integracoes/fontes/{f.pk}/sincronizar/")

    assert r.status_code == 400
    f.refresh_from_db()
    assert "Não achei nenhum treino" in f.ultimo_erro


def test_cadastro_de_fonte_e_so_para_admin(api, api_admin, criar_membro):
    r = api_admin.post("/api/integracoes/fontes/", {
        "nome": "Treinos 26.1", "destino": "esportes_treinos",
        "planilha": "https://docs.google.com/spreadsheets/d/1zTN/edit",
    }, format="json")
    assert r.status_code == 201, r.content
    assert r.json()["destino_rotulo"] == "Esportes: treinos e jogos"
    opcoes = api_admin.get("/api/integracoes/fontes/opcoes/").json()
    assert {"valor": "esportes_orcamento", "rotulo": "Esportes: orçamento"} in opcoes["destinos"]

    api.force_login(criar_membro(PERFIL_DIRETORIA))
    assert api.get("/api/integracoes/fontes/").status_code == 403


def test_comando_agendado_tambem_roda_esportes(planilhas_falsas):
    import io

    from django.core.management import call_command

    fonte(FontePlanilha.Destino.ESPORTES_ORCAMENTO, nome="A orçamento")
    fonte(FontePlanilha.Destino.ESPORTES_TREINOS, nome="B treinos")
    saida = io.StringIO()

    call_command("importar_planilhas", stdout=saida, stderr=io.StringIO())

    assert OrcamentoModalidade.objects.count() == 8 and Sessao.objects.count() == 8
    assert "aviso:" in saida.getvalue()
