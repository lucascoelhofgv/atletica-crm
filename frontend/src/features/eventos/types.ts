import type { Opcao } from "@/features/clientes/types";

export interface Financeiro {
  orcamento_previsto: number;
  ingressos_previstos: number;
  ingressos_vendidos: number;
  receita_ingressos: number;
  receita_ingressos_prevista: number;
  receita_extra: number;
  receita_total: number;
  custo_total: number;
  custo_pago: number;
  custo_a_pagar: number;
  resultado: number;
  margem: number | null;
  publico_estimado: number;
  custo_por_pessoa: number | null;
  ticket_medio: number | null;
  breakeven_ingressos: number | null;
}

export interface Lote {
  id: number;
  nome: string;
  quantidade_prevista: number;
  quantidade_vendida: number;
  valor_unitario: number;
  ordem: number;
  total_previsto: number;
  total_vendido: number;
}

export interface FornecedorMini {
  id: number;
  nome: string;
  nome_fantasia: string;
  nome_exibicao: string;
}

export interface Custo {
  id: number;
  tipo: "fixo" | "variavel";
  tipo_rotulo: string;
  item: string;
  quantidade: number;
  valor_unitario: number;
  valor_pago: number;
  situacao: "pendente" | "parcial" | "pago";
  situacao_rotulo: string;
  fornecedor: FornecedorMini | null;
  observacao: string;
  valor_total: number;
}

export interface Receita {
  id: number;
  origem: string;
  origem_rotulo: string;
  descricao: string;
  valor: number;
  recebido: boolean;
}

export interface EventoLista {
  id: number;
  nome: string;
  tipo: string;
  tipo_rotulo: string;
  data: string;
  horario: string;
  local: string;
  status: "planejamento" | "confirmado" | "realizado" | "cancelado";
  status_rotulo: string;
  capacidade: number | null;
  responsavel: { id: number; nome: string } | null;
  financeiro: Financeiro;
}

export interface Evento extends EventoLista {
  descricao: string;
  publico_realizado: number | null;
  staff_cortesias: number;
  publico_alvo: string;
  link_inscricao: string;
  orcamento_previsto: number;
  fornecedores: FornecedorMini[];
  observacoes: string;
  criado_em: string;
  criado_por: { id: number; nome: string } | null;
  lotes: Lote[];
  custos: Custo[];
  receitas: Receita[];
}

export interface EventoEntrada {
  nome: string;
  tipo: string;
  descricao: string;
  data: string;
  horario: string;
  local: string;
  capacidade: number | null;
  publico_realizado: number | null;
  staff_cortesias: number;
  status: string;
  publico_alvo: string;
  link_inscricao: string;
  orcamento_previsto: number;
  responsavel_id: number | null;
  fornecedores_ids: number[];
  observacoes: string;
}

export type LoteEntrada = Omit<Lote, "id" | "total_previsto" | "total_vendido">;
export type CustoEntrada = Omit<Custo, "id" | "tipo_rotulo" | "situacao_rotulo" | "fornecedor" | "valor_total"> & { fornecedor_id: number | null };
export type ReceitaEntrada = Omit<Receita, "id" | "origem_rotulo">;

export interface OpcoesEvento {
  tipos: Opcao[];
  status: Opcao[];
  tipos_custo: Opcao[];
  situacoes_custo: Opcao[];
  origens_receita: Opcao[];
  membros: { id: number; nome: string }[];
  fornecedores: FornecedorMini[];
}

export interface FiltrosEventos {
  q?: string;
  tipo?: string;
  status?: string;
  futuros?: boolean;
  pagina?: number;
}
