from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import ItemPedido, Pagamento, Pedido


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1
    autocomplete_fields = ("produto",)


class PagamentoInline(admin.TabularInline):
    model = Pagamento
    extra = 0


@admin.register(Pedido)
class PedidoAdmin(SimpleHistoryAdmin):
    list_display = ("numero", "cliente", "status", "status_pagamento",
                    "valor_total", "data_compra", "responsavel")
    list_filter = ("status", "status_pagamento", "forma_pagamento")
    search_fields = ("numero", "cliente__nome")
    date_hierarchy = "data_compra"
    autocomplete_fields = ("cliente",)
    inlines = [ItemPedidoInline, PagamentoInline]
    readonly_fields = ("numero", "estoque_baixado", "criado_em", "atualizado_em")
