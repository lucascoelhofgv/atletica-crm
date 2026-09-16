import type { Distribuicao, PeriodoResolvido } from "@/features/dashboard/types";

export interface LinhaVendas {
  data: string;
  total: number;
  qtd: number;
  anterior?: number | null;
  qtd_anterior?: number | null;
}

export interface RelVendas {
  periodo: PeriodoResolvido;
  total: number;
  qtd: number;
  ticket_medio: number;
  total_anterior: number | null;
  qtd_anterior: number | null;
  por_periodo: LinhaVendas[];
  por_status: Distribuicao[];
  por_forma: Distribuicao[];
}

export interface ItemProdutoVendido {
  produto_id: number;
  produto: string;
  tamanho: string;
  categoria: string;
  sku: string;
  qtd: number;
  receita: number;
  pedidos: number;
  /** Fração da receita total (0.25 = 25 %). */
  participacao: number;
}

export interface RelProdutos {
  periodo: PeriodoResolvido;
  itens: ItemProdutoVendido[];
  total_qtd: number;
  total_receita: number;
}

export type SituacaoEstoque = "ok" | "baixo" | "esgotado";

export interface ItemEstoque {
  id: number;
  nome: string;
  tamanho: string;
  categoria: string;
  sku: string;
  saldo: number;
  minimo: number;
  custo_unitario: number;
  preco_venda: number;
  valor_em_estoque: number;
  situacao: SituacaoEstoque;
  url: string;
}

export interface RelEstoque {
  itens: ItemEstoque[];
  valor_total: number;
  unidades: number;
  resumo: Record<SituacaoEstoque, number>;
}

export interface ItemCliente {
  id: number;
  nome: string;
  email: string;
  curso: string;
  categoria: string;
  pedidos: number;
  gasto: number;
  url: string;
}

export interface RelClientes {
  itens: ItemCliente[];
  total: number;
}
