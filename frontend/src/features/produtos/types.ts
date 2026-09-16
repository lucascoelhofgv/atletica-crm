import type { Opcao } from "@/features/clientes/types";

export interface CategoriaProduto {
  id: number;
  nome: string;
  descricao?: string;
  ativo?: boolean;
}

export interface FornecedorResumo {
  id: number;
  nome: string;
  nome_fantasia: string;
}

export type Situacao = "ok" | "baixo" | "esgotado";

export interface ProdutoLista {
  id: number;
  nome: string;
  nome_completo: string;
  tamanho: string;
  cor: string;
  sku: string;
  codigo_interno: string;
  categoria: CategoriaProduto | null;
  fornecedor: FornecedorResumo | null;
  foto: string | null;
  custo_unitario: number;
  preco_venda: number;
  quantidade_atual: number;
  estoque_minimo: number;
  situacao: Situacao;
  valor_em_estoque: number;
  margem_estimada: number | null;
  status: "ativo" | "inativo";
  status_rotulo: string;
}

export interface Movimentacao {
  id: number;
  produto: number;
  produto_nome: string;
  tipo: string;
  tipo_rotulo: string;
  eh_entrada: boolean;
  quantidade: number;
  saldo_apos: number | null;
  data: string;
  usuario: { id: number; nome: string } | null;
  motivo: string;
  pedido: number | null;
  pedido_numero: string | null;
  observacao: string;
}

export interface Produto extends ProdutoLista {
  descricao: string;
  marca: string;
  estoque_maximo: number | null;
  localizacao: string;
  observacoes: string;
  criado_em: string;
  criado_por: { id: number; nome: string } | null;
  movimentacoes_recentes: Movimentacao[];
}

export interface ProdutoEntrada {
  nome: string;
  codigo_interno: string;
  sku: string;
  categoria_id: number | null;
  descricao: string;
  tamanho: string;
  cor: string;
  marca: string;
  fornecedor_id: number | null;
  custo_unitario: number;
  preco_venda: number;
  estoque_minimo: number;
  estoque_maximo: number | null;
  localizacao: string;
  status: "ativo" | "inativo";
  observacoes: string;
}

export interface MovimentacaoEntrada {
  tipo: string;
  quantidade: number;
  motivo?: string;
  observacao?: string;
}

export interface OpcoesProduto {
  categorias: CategoriaProduto[];
  fornecedores: FornecedorResumo[];
  status: Opcao[];
  tipos_movimentacao: Opcao[];
}

export interface FiltrosProdutos {
  q?: string;
  categoria?: number;
  fornecedor?: number;
  status?: string;
  situacao?: Situacao;
  pagina?: number;
  ordenar?: string;
}
