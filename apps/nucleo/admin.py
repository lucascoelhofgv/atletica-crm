from django.contrib import admin

from .models import Configuracao, FontePlanilha, LogAcesso, RegistroAtividade


@admin.register(Configuracao)
class ConfiguracaoAdmin(admin.ModelAdmin):
    list_display = ("nome_organizacao", "titulo_app", "atualizado_em")

    def has_add_permission(self, request):
        return not Configuracao.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(FontePlanilha)
class FontePlanilhaAdmin(admin.ModelAdmin):
    list_display = ("nome", "destino", "ativa", "ultima_sincronizacao", "ultimo_erro")
    list_filter = ("destino", "ativa")
    search_fields = ("nome", "planilha")
    readonly_fields = ("ultima_sincronizacao", "ultimo_resultado", "ultimo_erro",
                       "criado_em", "criado_por")


@admin.register(RegistroAtividade)
class RegistroAtividadeAdmin(admin.ModelAdmin):
    list_display = ("criado_em", "usuario", "verbo", "alvo")
    list_filter = ("verbo",)
    search_fields = ("alvo", "descricao", "usuario__username")
    date_hierarchy = "criado_em"


@admin.register(LogAcesso)
class LogAcessoAdmin(admin.ModelAdmin):
    list_display = ("momento", "usuario", "sucesso", "ip")
    list_filter = ("sucesso",)
    search_fields = ("usuario__username", "ip")
    date_hierarchy = "momento"
