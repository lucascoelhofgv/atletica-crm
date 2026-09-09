from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import CategoriaProduto, MovimentacaoEstoque, Produto


@admin.register(Produto)
class ProdutoAdmin(SimpleHistoryAdmin):
    list_display = ("nome", "sku", "categoria", "quantidade_atual", "estoque_minimo",
                    "preco_venda", "status")
    list_filter = ("status", "categoria", "fornecedor")
    search_fields = ("nome", "codigo_interno", "sku", "marca")
    autocomplete_fields = ("categoria", "fornecedor")
    readonly_fields = ("quantidade_atual", "criado_em")


@admin.register(CategoriaProduto)
class CategoriaProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo")
    search_fields = ("nome",)


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ("data", "produto", "tipo", "quantidade", "saldo_apos", "usuario")
    list_filter = ("tipo",)
    search_fields = ("produto__nome", "motivo")
    date_hierarchy = "data"
    readonly_fields = ("saldo_apos", "data")
