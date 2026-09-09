from django.urls import path

from . import views

app_name = "vendas"

urlpatterns = [
    path("", views.PedidoListView.as_view(), name="pedido_lista"),
    path("novo/", views.pedido_novo, name="pedido_novo"),
    path("<int:pk>/", views.PedidoDetailView.as_view(), name="pedido_detalhe"),
    path("<int:pk>/editar/", views.pedido_editar, name="pedido_editar"),
    path("<int:pk>/status/", views.mudar_status, name="pedido_status"),
    path("<int:pk>/pagamento/", views.registrar_pagamento, name="pedido_pagamento"),
    path("<int:pk>/recibo/", views.pedido_recibo, name="pedido_recibo"),
]
