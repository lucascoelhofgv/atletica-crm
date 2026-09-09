# Guia do Administrador

## Perfis de acesso

Os perfis são **Grupos** do Django. Cada um dá um conjunto de permissões:

| Perfil | Pode |
|---|---|
| **Administrador** | tudo: módulos, usuários, permissões, identidade visual, exclusões, histórico, exportações |
| **Diretoria** | ver indicadores; gerenciar clientes, pedidos, tarefas; acompanhar estoque e fornecedores; relatórios |
| **Operacional** | registrar vendas, atualizar pedidos, consultar produtos, atender clientes, tarefas atribuídas |
| **Estoque** | cadastrar produtos, registrar entradas/saídas/ajustes, estoque mínimo, inventário |
| **Financeiro** | ver pedidos, registrar pagamentos, contas a receber, relatórios financeiros |
| **Visualização** | somente leitura de dados e dashboards |

Um membro pode ter **mais de um perfil**. O acesso é o somatório das permissões.

### Criar um novo perfil

Django Admin → **Grupos** → Adicionar. Selecione as permissões desejadas
(`view_`, `add_`, `change_`, `delete_` por modelo). O novo grupo aparece
automaticamente na tela de cadastro de membros.

## Criar um membro

1. Menu **Membros → + Novo membro**.
2. Preencha usuário, nome, e-mail, cargo e defina uma senha provisória.
3. Marque um ou mais **Perfis de acesso**.
4. Oriente a pessoa a trocar a senha no primeiro acesso (menu do usuário →
   "Alterar senha").

## Desligar um membro

Menu **Membros** → botão **Desativar** na linha da pessoa. Isso:
- bloqueia o login imediatamente;
- preenche a data de saída;
- **mantém** todo o histórico e os registros criados por ela.

Nunca exclua um membro que já usou o sistema — apenas desative.

## Identidade visual

Menu **Identidade visual**: logo, favicon, banner, cores primária/secundária,
nome e dados institucionais. As mudanças valem para todos na hora seguinte.

## Histórico e auditoria

- **Histórico de atividades** (menu Histórico): ações relevantes com usuário,
  data e link para o registro.
- **Logs de acesso**: entradas no sistema (sucesso e falha), IP e dispositivo.
- No **Django Admin**, cada Cliente / Produto / Pedido / Fornecedor / Membro tem
  aba **History** com o valor anterior e o novo de cada campo alterado.

## Backup

### Banco (Supabase)
- Supabase mantém backups automáticos diários (plano free: retenção curta).
- Backup manual sob demanda:
  ```bash
  python manage.py dumpdata --natural-primary --natural-foreign \
    -e contenttypes -e auth.permission -e admin.logentry -e sessions \
    --indent 2 > backup_$(date +%F).json
  ```
  Restaurar: `python manage.py loaddata backup_AAAA-MM-DD.json`.

### Exportações rápidas
- Clientes: **Clientes → Exportar**.
- Inventário: **Produtos → Exportar inventário**.
- Relatórios: botão **Exportar CSV** em cada relatório.
- Tudo de uma vez: integração **Google Sheets** (abas Clientes/Produtos/Pedidos).

### Recomendação
Rodar `dumpdata` (ou `exportar_sheets`) **semanalmente** e guardar o arquivo fora
do Render/Supabase (Drive da Atlética). Agende com um Cron Job do Render.

## LGPD — pontos de atenção

- Colete só o necessário. CPF e data de nascimento são opcionais.
- O campo "autoriza receber comunicações" registra o consentimento do cliente.
- Para atender a um pedido de exclusão de dados: anonimize o cliente (troque nome
  por "Removido a pedido", limpe e-mail/telefone/CPF) em vez de apagar, para não
  quebrar o histórico de pedidos. Exclusão total só pelo Administrador.
- Não divulgue exportações com dados pessoais fora da diretoria.
