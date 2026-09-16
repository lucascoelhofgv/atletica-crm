from django.urls import path

from . import views

app_name = "vendas"

urlpatterns = [
    path("<int:pk>/recibo/", views.pedido_recibo, name="pedido_recibo"),
]
