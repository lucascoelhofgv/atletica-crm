# CRM Atlética FGV Rio

Sistema web de gestão para a Atlética: clientes, produtos e estoque, pedidos e
vendas, fornecedores, tarefas, relatórios e histórico — com controle de acesso
por perfil e identidade visual configurável.

Feito para sobreviver a trocas de diretoria: os dados ficam centralizados, todas
as alterações relevantes são registradas, e quem sai é **desativado** sem apagar
o histórico.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Django 5 (Python 3.12) |
| Banco | PostgreSQL em produção (Supabase free) · SQLite no dev |
| Auth / perfis | Django auth + Grupos (6 perfis) |
| Auditoria | django-simple-history |
| Frontend | Templates Django + Bootstrap 5 + HTMX + SortableJS (sem build de Node) |
| Arquivos | armazenamento local no dev; Supabase Storage/R2 em produção |
| Integração | Google Sheets (gspread) |
| Deploy | Render (web, free) + Supabase (Postgres, free) + WhiteNoise |

## Módulos

- **Painel** — KPIs por período, produtos mais vendidos, tarefas, atividades.
- **Clientes (CRM)** — cadastro completo, categorias, tags, interações,
  importação/exportação CSV, filtros.
- **Produtos e estoque** — ficha do produto, movimentações rastreadas (entrada,
  saída, ajuste, perda, devolução), alertas de estoque baixo/esgotado, inventário.
- **Pedidos e vendas** — itens, pagamentos, status com **baixa automática de
  estoque** e estorno, recibo para impressão/PDF.
- **Fornecedores** — cadastro, categorias, avaliação (preço, qualidade, prazo…).
- **Tarefas** — lista, quadro Kanban com arrastar-e-soltar, comentários,
  vínculo com cliente/pedido/fornecedor.
- **Relatórios** — vendas por período, produtos vendidos, estoque, clientes;
  exportação CSV.
- **Administração** — membros e perfis, identidade visual, histórico de
  atividades, logs de acesso, Django Admin para manutenção avançada.

## Perfis de acesso

`Administrador` · `Diretoria` · `Operacional` · `Estoque` · `Financeiro` ·
`Visualização` (somente leitura). Novos perfis podem ser criados como Grupos no
Django Admin.

---

## Rodando localmente (Windows)

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .env.example .env          # e ajuste SECRET_KEY; deixe DEBUG=True
.venv\Scripts\python manage.py migrate
.venv\Scripts\python manage.py seed_inicial --com-demo
.venv\Scripts\python manage.py createsuperuser
.venv\Scripts\python manage.py shell -c "from django.contrib.auth import get_user_model as u; from django.contrib.auth.models import Group as g; x=u().objects.order_by('-id').first(); x.groups.add(g.objects.get(name='Administrador'))"
.venv\Scripts\python manage.py runserver
```

Acesse http://127.0.0.1:8000 e entre com o usuário criado.

Para remover os dados de demonstração: `python manage.py seed_inicial --remover-demo`.

## Documentação

- [`docs/INSTALACAO.md`](docs/INSTALACAO.md) — instalação passo a passo.
- [`docs/DEPLOY.md`](docs/DEPLOY.md) — publicação (Render + Supabase) e Google Sheets.
- [`docs/ADMINISTRADOR.md`](docs/ADMINISTRADOR.md) — criar usuários, perfis, backup.
- [`docs/MANUAL.md`](docs/MANUAL.md) — manual de uso do dia a dia.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — o que já existe e o que vem depois.

## Aviso

O módulo financeiro/relatórios tem finalidade de **controle gerencial interno** e
não substitui contabilidade, obrigações fiscais ou orientação profissional.
