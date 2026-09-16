"""Paginação padrão da API.

Resposta: ``{"total", "pagina", "paginas", "resultados"}``.
Parâmetros: ``?pagina=2&tamanho=50`` (máximo 200 por página).
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class PaginacaoPadrao(PageNumberPagination):
    page_size = 30
    page_query_param = "pagina"
    page_size_query_param = "tamanho"
    max_page_size = 200

    def get_paginated_response(self, data):
        return Response(
            {
                "total": self.page.paginator.count,
                "pagina": self.page.number,
                "paginas": self.page.paginator.num_pages,
                "resultados": data,
            }
        )
