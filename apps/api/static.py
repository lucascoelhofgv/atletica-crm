"""Teste de imutabilidade para o WhiteNoise.

O Vite já gera nomes com hash (``index-DkQ1s3Ab.js``). O ``index.html`` aponta
para esses nomes, não para a cópia re-hasheada pelo Django, então o WhiteNoise
precisa saber que eles também podem receber ``Cache-Control: immutable``.
Sem parâmetros de app: importado por ``config/settings.py`` antes dos apps
carregarem.
"""

import re

# Assets do Vite: /static/app/assets/<nome>-<hash de 8+ chars>.<ext>
_VITE = re.compile(r"/app/assets/[^/]+-[A-Za-z0-9_-]{8,}\.[A-Za-z0-9]+$")
# Padrão do ManifestStaticFilesStorage do Django: <nome>.<12 hex>.<ext>
_DJANGO = re.compile(r"\.[0-9a-f]{12}\.[A-Za-z0-9]+$")


def eh_imutavel(path, url):
    url = url.replace("\\", "/")
    return bool(_VITE.search(url) or _DJANGO.search(url))
