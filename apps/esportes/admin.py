from django.contrib import admin

from .models import Modalidade, OrcamentoModalidade, Sessao


class OrcamentoInline(admin.TabularInline):
    model = OrcamentoModalidade
    extra = 0


@admin.register(Modalidade)
class ModalidadeAdmin(admin.ModelAdmin):
    list_display = ("nome", "dia_semana", "horario_inicio", "local")
    list_filter = ("esporte", "naipe")
    inlines = [OrcamentoInline]


@admin.register(OrcamentoModalidade)
class OrcamentoModalidadeAdmin(admin.ModelAdmin):
    list_display = ("modalidade", "ano", "semestre", "treinos_previstos",
                    "jogos_previstos", "total_previsto")
    list_filter = ("ano", "semestre", "modalidade__esporte")

    @admin.display(description="Total previsto")
    def total_previsto(self, obj):
        return obj.total_previsto


@admin.register(Sessao)
class SessaoAdmin(admin.ModelAdmin):
    list_display = ("data", "modalidade", "tipo", "confirmada", "teve_tecnico",
                    "teve_quadra", "custo", "observacao")
    list_filter = ("tipo", "confirmada", "modalidade__esporte", "modalidade__naipe")
    date_hierarchy = "data"
    search_fields = ("observacao", "origem")
