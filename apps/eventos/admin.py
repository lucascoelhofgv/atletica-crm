from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import CustoEvento, Evento, LoteIngresso, ReceitaEvento


class LoteInline(admin.TabularInline):
    model = LoteIngresso
    extra = 1


class CustoInline(admin.TabularInline):
    model = CustoEvento
    extra = 1
    autocomplete_fields = ("fornecedor",)


class ReceitaInline(admin.TabularInline):
    model = ReceitaEvento
    extra = 0


@admin.register(Evento)
class EventoAdmin(SimpleHistoryAdmin):
    list_display = ("nome", "tipo", "data", "status", "ingressos_vendidos",
                    "receita_total", "custo_total", "resultado")
    list_filter = ("tipo", "status")
    search_fields = ("nome", "local")
    date_hierarchy = "data"
    inlines = [LoteInline, CustoInline, ReceitaInline]
    filter_horizontal = ("fornecedores",)

    @admin.display(description="Receita total")
    def receita_total(self, obj):
        return obj.receita_total

    @admin.display(description="Custo total")
    def custo_total(self, obj):
        return obj.custo_total

    @admin.display(description="Resultado")
    def resultado(self, obj):
        return obj.resultado

    @admin.display(description="Ingressos vendidos")
    def ingressos_vendidos(self, obj):
        return obj.ingressos_vendidos
