import type { Opcao } from "@/features/clientes/types";

export type StatusPedido =
  | "rascunho"
  | "aguardando_pagamento"
  | "pago"
  | "em_separacao"
  | "pronto"
  | "entregue"
  | "cancelado"
  | "devolvido";

export interface ClienteResumo {
  id: number;
  nome: string;
  nome_social: string;
  email: string;
  whatsapp: string;
  telefone: string;
}

export interface ProdutoItem {
  id: number;
  nome: string;
  nome_completo: string;
  tamanho: string;
  sku: string;
  preco_venda: number;
  quantidade_atual: number;
  status: string;
  foto: string | null;
}

export interface ItemPedido {
  id: number;
  produto: ProdutoItem;
  quantidade: number;
  preco_unitario: number;
  desconto_item: number;
  total: number;
}

export interface Pagamento {
  id: number;
  valor: number;
  forma: string;
  forma_rotulo: string;
  data: string;
  observacao: string;
  registrado_por: { id: number; nome: string } | null;
  criado_em: string;
}

export interface Falta {
  produto_id: number;
  produto: string;
  necessario: number;
  disponivel: number;
}

export interface PedidoLista {
  id: number;
  numero: string | null;
  cliente: ClienteResumo;
  status: StatusPedido;
  status_rotulo: string;
  status_pagamento: "pendente" | "parcial" | "quitado";
  status_pagamento_rotulo: string;
  forma_pagamento: string;
  forma_pagamento_rotulo: string;
  valor_total: number;
  total_pago: number;
  saldo_devedor: number;
  data_compra: string;
  data_entrega: string | null;
  responsavel: { id: number; nome: string } | null;
  qtd_itens: number;
  estoque_baixado: boolean;
  criado_em: string;
}

export interface Pedido extends Omit<PedidoLista, "qtd_itens"> {
  desconto: number;
  taxa: number;
  subtotal: number;
  local_retirada: string;
  observacoes: string;
  comprovante: string | null;
  criado_por: { id: number; nome: string } | null;
  atualizado_em: string;
  itens: ItemPedido[];
  pagamentos: Pagamento[];
  faltas: Falta[];
  url_recibo: string;
}

export interface ItemEntrada {
  id?: number;
  produto: number;
  quantidade: number;
  preco_unitario: number | null;
  desconto_item: number;
}

export interface PedidoEntrada {
  cliente: number;
  status: StatusPedido;
  forma_pagamento: string;
  desconto: number;
  taxa: number;
  data_compra: string;
  data_entrega: string | null;
  local_retirada: string;
  responsavel: number | null;
  observacoes: string;
  itens: ItemEntrada[];
}

export interface OpcoesPedido {
  status: Opcao[];
  formas_pagamento: Opcao[];
  status_pagamento: Opcao[];
  membros: { id: number; nome: string }[];
}

export interface FiltrosPedidos {
  q?: string;
  status?: string;
  status_pagamento?: string;
  forma_pagamento?: string;
  cliente?: number;
  pagina?: number;
  ordenar?: string;
}
