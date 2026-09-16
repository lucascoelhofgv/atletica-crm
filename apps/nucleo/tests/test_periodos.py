from datetime import date

from apps.nucleo.services.periodos import (
    Periodo, eixo, intervalo_preset, preencher_serie, resolver,
)

HOJE = date(2026, 9, 15)


def test_presets_seguem_a_regra_antiga():
    assert intervalo_preset("hoje", HOJE) == (HOJE, HOJE)
    assert intervalo_preset("7d", HOJE) == (date(2026, 9, 8), HOJE)
    assert intervalo_preset("30d", HOJE) == (date(2026, 8, 16), HOJE)
    assert intervalo_preset("semestre", HOJE) == (date(2026, 7, 1), HOJE)
    assert intervalo_preset("ano", HOJE) == (date(2026, 1, 1), HOJE)
    assert intervalo_preset("semestre", date(2026, 3, 3)) == (date(2026, 1, 1), date(2026, 3, 3))


def test_resolver_padrao_e_invalido():
    assert resolver({}, HOJE).chave == "30d"
    assert resolver({"periodo": "xyz"}, HOJE).chave == "30d"
    assert resolver({"periodo": "custom"}, HOJE).chave == "30d"  # custom sem datas


def test_resolver_custom_inverte_e_rotula():
    p = resolver({"periodo": "custom", "inicio": "2026-09-10", "fim": "2026-09-01",
                  "comparar": "1"}, HOJE)
    assert (p.inicio, p.fim) == (date(2026, 9, 1), date(2026, 9, 10))
    assert p.comparar is True
    assert p.rotulo == "01/09/2026 a 10/09/2026"
    assert p.dias == 10


def test_periodo_anterior_tem_mesma_duracao():
    p = Periodo("custom", "", date(2026, 9, 1), date(2026, 9, 10))
    assert (p.anterior_inicio, p.anterior_fim) == (date(2026, 8, 22), date(2026, 8, 31))
    assert p.anterior.dias == p.dias


def test_granularidade():
    assert Periodo("x", "", date(2026, 1, 1), date(2026, 4, 30)).granularidade == "dia"
    assert Periodo("x", "", date(2026, 1, 1), date(2026, 7, 19)).granularidade == "mes"


def test_eixo_e_zero_fill():
    assert len(eixo(date(2026, 9, 8), date(2026, 9, 15), "dia")) == 8
    meses = eixo(date(2026, 1, 15), date(2026, 4, 2), "mes")
    assert meses == [date(2026, 1, 1), date(2026, 2, 1), date(2026, 3, 1), date(2026, 4, 1)]
    serie = preencher_serie({date(2026, 9, 10): 5}, date(2026, 9, 8), date(2026, 9, 12), "dia")
    assert [v for _, v in serie] == [0, 0, 5, 0, 0]
