# Roadmap

## Entregue (MVP — Fase 1)

- [x] Login, recuperação de senha, sessão segura
- [x] 6 perfis de acesso + criação de novos perfis
- [x] Gestão de membros (criar, editar, desativar sem perder histórico)
- [x] Dashboard com indicadores por período
- [x] Clientes (CRM): CRUD, categorias, tags, interações, import/export CSV, filtros
- [x] Produtos e estoque: CRUD, movimentações rastreadas, alertas, inventário, export
- [x] Pedidos: itens, pagamentos, status com baixa/estorno automático de estoque, recibo
- [x] Fornecedores: CRUD, categorias, avaliação
- [x] Tarefas: lista + quadro Kanban (arrastar), comentários, vínculos
- [x] Relatórios básicos + exportação CSV
- [x] Identidade visual configurável (logo, cores, favicon, dados)
- [x] Histórico de atividades + logs de acesso + auditoria campo a campo (Django Admin)
- [x] Busca global
- [x] Integração Google Sheets (exportação/sincronização manual e agendável)
- [x] **Eventos e festas**: lotes de ingresso, custos fixos/variáveis, receitas
      extras, resultado (lucro/prejuízo), margem, ticket médio, custo por pessoa,
      breakeven — modelado a partir das planilhas Jungle / FRAT HOUSE
- [x] Aba **Festas** no Google Sheets (uma linha por festa, para análise ano a ano)
- [x] Dados de demonstração removíveis
- [x] Layout responsivo (celular/tablet/desktop)

## Fase 2

- [ ] Módulo **Financeiro operacional** completo (receitas/despesas, centros de
      custo, contas a receber, anexos de comprovante)
- [ ] **Pipelines** visuais configuráveis (vendas, patrocínio, parcerias)
- [ ] Notificações (tarefas vencendo, pedidos pendentes) — in-app e e-mail
- [ ] Storage S3-compatível para uploads persistentes
- [ ] Importação/exportação avançada (mapeamento de colunas, atualização em massa)
- [ ] Importador de Fornecedores por CSV (para a planilha "Relação com Empresas")
- [ ] Puxar dados do Google Sheets de volta para o CRM (hoje a sincronização é só de saída)
- [ ] Relatórios avançados com gráficos

## Fase 3

- [ ] Integração WhatsApp (envio de confirmação de pedido / cobrança)
- [ ] Integração com gateway de pagamento (PIX automático)
- [ ] PWA / uso offline básico
- [ ] Leitura de QR Code para retirada de pedido
- [ ] Programa de fidelidade
- [ ] Automação de comunicação (réguas de e-mail)

## Dívidas técnicas conhecidas

- Uploads no Render free são efêmeros (resolver com django-storages + R2/Supabase).
- `pedido_form` adiciona 3 linhas de item fixas; falta botão "adicionar mais linhas"
  dinâmico (JS) e autopreenchimento do preço ao escolher o produto.
- Testes automatizados ainda não escritos (só verificação manual das regras de estoque).
- Recibo em PDF é via "imprimir do navegador"; avaliar geração server-side (reportlab).
