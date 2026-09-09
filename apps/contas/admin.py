from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import Membro


@admin.register(Membro)
class MembroAdmin(UserAdmin, SimpleHistoryAdmin):
    list_display = ("username", "nome_exibicao", "email", "cargo", "is_active",
                    "is_staff")
    list_filter = ("is_active", "is_staff", "groups")
    search_fields = ("username", "first_name", "last_name", "email", "cargo")
    fieldsets = UserAdmin.fieldsets + (
        ("Dados da Atlética", {
            "fields": ("cargo", "telefone", "foto", "data_entrada", "data_saida",
                       "observacoes")
        }),
    )
