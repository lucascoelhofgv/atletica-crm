from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import AvaliacaoFornecedor, Fornecedor


class AvaliacaoInline(admin.TabularInline):
    model = AvaliacaoFornecedor
    extra = 0


@admin.register(Fornecedor)
class FornecedorAdmin(SimpleHistoryAdmin):
    list_display = ("nome", "nome_fantasia", "categoria", "status", "contato_nome",
                    "telefone")
    list_filter = ("categoria", "status")
    search_fields = ("nome", "nome_fantasia", "contato_nome", "documento")
    inlines = [AvaliacaoInline]


@admin.register(AvaliacaoFornecedor)
class AvaliacaoFornecedorAdmin(admin.ModelAdmin):
    list_display = ("fornecedor", "media", "autor", "criado_em")
    search_fields = ("fornecedor__nome",)
