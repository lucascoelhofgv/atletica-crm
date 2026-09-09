# Manual de uso — dia a dia

## Entrar

Acesse o endereço do sistema, informe **usuário** e **senha**. Esqueceu a senha?
"Esqueci minha senha" na tela de login (o link chega por e-mail).

## Painel

Mostra o resumo do período escolhido (canto superior direito): vendas, receita,
pedidos por situação, alertas de estoque, clientes, tarefas atrasadas. Os cartões
vermelhos são alertas que pedem ação.

## Clientes

- **+ Novo cliente**: nome é o único campo obrigatório; o resto ajuda a
  segmentar depois.
- Na ficha do cliente você registra **interações** (ligação, WhatsApp, e-mail…)
  e vê o **histórico de pedidos**.
- **Importar CSV**: para trazer uma lista pronta (uma coluna `nome` no mínimo).
- **Filtros**: por categoria, relacionamento, comunidade FGV, ou busca livre.

## Produtos e estoque

- **+ Novo produto**: cadastre a ficha (preço, custo, estoque mínimo…). O saldo
  começa em zero.
- Para lançar o estoque inicial ou qualquer ajuste, abra o produto e use
  **Movimentar estoque**: escolha o tipo (entrada, saída para evento, perda,
  ajuste, devolução…), a quantidade e o motivo. Cada movimentação fica no
  histórico com data e responsável.
- Alertas aparecem quando o saldo fica **abaixo do mínimo** ou **zera**.

## Pedidos

1. **+ Novo pedido** → escolha o cliente, adicione os itens (produto +
   quantidade; o preço vem sugerido).
2. Salve. O pedido nasce como **rascunho** (não mexe no estoque).
3. Mude o **status**:
   - `Aguardando pagamento` → ainda não baixa estoque.
   - `Pago` / `Em separação` / `Pronto` / `Entregue` → **baixa o estoque
     automaticamente** (uma vez só).
   - `Cancelado` / `Devolvido` → **devolve** o estoque.
   - Se não houver saldo suficiente, o sistema **bloqueia** a confirmação e avisa
     o que está faltando.
4. Registre **pagamentos** (total ou parcial) na própria tela do pedido.
5. **Recibo / imprimir**: gera um resumo para imprimir ou salvar em PDF
   (Ctrl+P → "Salvar como PDF").

## Fornecedores

Cadastro com contato, categoria e condições. Na ficha dá para **avaliar** o
fornecedor (preço, qualidade, prazo, atendimento, confiabilidade) e ver os
produtos vinculados a ele.

## Tarefas

- **Lista** com filtros (minhas, atrasadas, por status).
- **Quadro** (Kanban): arraste o cartão entre as colunas para mudar o status.
- Cada tarefa aceita **comentários** e pode ser ligada a um cliente, pedido ou
  fornecedor.

## Relatórios

Vendas por período, produtos mais/menos vendidos, estoque atual, clientes e
recorrência. Todos com filtro de data e botão **Exportar CSV** (abre no Excel).

## Busca

A barra no topo procura ao mesmo tempo em clientes, produtos, pedidos,
fornecedores, tarefas e membros.

## Dicas

- Ações que apagam algo pedem confirmação.
- Mensagens verdes = deu certo; vermelhas = algo precisa ser corrigido.
- Seu perfil define o que você vê e edita. Se faltar acesso, fale com um
  Administrador.
