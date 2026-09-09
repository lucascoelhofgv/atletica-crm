from django.contrib import admin

from .models import ComentarioTarefa, Tarefa


class ComentarioInline(admin.TabularInline):
    model = ComentarioTarefa
    extra = 0


@admin.register(Tarefa)
class TarefaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "status", "prioridade", "responsavel", "prazo",
                    "atrasada")
    list_filter = ("status", "prioridade", "responsavel")
    search_fields = ("titulo", "descricao")
    date_hierarchy = "criado_em"
    inlines = [ComentarioInline]
