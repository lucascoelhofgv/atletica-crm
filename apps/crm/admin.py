from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import CategoriaCliente, Cliente, Interacao, Tag


class InteracaoInline(admin.TabularInline):
    model = Interacao
    extra = 0


@admin.register(Cliente)
class ClienteAdmin(SimpleHistoryAdmin):
    list_display = ("nome", "categoria", "relacionamento", "curso", "membro_fgv",
                    "email", "telefone")
    list_filter = ("relacionamento", "categoria", "membro_fgv", "vinculo", "tags")
    search_fields = ("nome", "nome_social", "email", "telefone", "whatsapp", "curso")
    autocomplete_fields = ("categoria",)
    filter_horizontal = ("tags",)
    inlines = [InteracaoInline]
    readonly_fields = ("criado_em", "atualizado_em")


@admin.register(CategoriaCliente)
class CategoriaClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "cor", "ativo")
    search_fields = ("nome",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("nome", "cor")
    search_fields = ("nome",)


@admin.register(Interacao)
class InteracaoAdmin(admin.ModelAdmin):
    list_display = ("cliente", "tipo", "resumo", "data", "registrado_por")
    list_filter = ("tipo",)
    search_fields = ("cliente__nome", "resumo")
