/** Payload de GET /api/dashboard/ (apps/nucleo/services/dashboard.py). */

export type Granularidade = "dia" | "mes";

export interface PeriodoResolvido {
  chave: string;
  rotulo: string;
  inicio: string;
  fim: string;
  dias: number;
  granularidade: Granularidade;
  comparar: boolean;
  anterior: { inicio: string; fim: string };
}

export interface Kpi {
  valor: number;
  anterior: number | null;
  /** Fração (0.12 = +12 %); null quando não há base de comparação. */
  variacao: number | null;
  serie: number[];
}

export interface PontoSerie {
  data: string;
  valor: number;
  anterior?: number | null;
}

export type NomeKpi = "receita" | "pedidos" | "clientes_novos" | "ticket_medio";

export interface Distribuicao {
  status?: string;
  forma?: string;
  rotulo: string;
  qtd: number;
  valor: number;
}

export interface TopProduto {
  nome: string;
  qtd: number;
  receita: number;
}

export interface Alertas {
  pedidos_aguardando: number;
  pedidos_retirada: number;
  produtos_baixo: number;
  produtos_esgotados: number;
  tarefas_atrasadas: number;
  fornecedores_ativos: number;
  clientes_total: number;
  valor_estoque: number;
}

export interface TarefaResumo {
  id: number;
  titulo: string;
  prazo: string | null;
  prioridade: string;
  prioridade_rotulo: string;
  status: string;
  status_rotulo: string;
  atrasada: boolean;
  url: string;
}

export interface EventoResumo {
  id: number;
  nome: string;
  data: string;
  tipo: string;
  tipo_rotulo: string;
  status: string;
  status_rotulo: string;
  ingressos_vendidos: number;
  receita_total: number;
  url: string;
}

export interface Atividade {
  id: number;
  usuario: { id: number; nome: string } | null;
  verbo: string;
  alvo: string;
  descricao: string;
  url: string;
  criado_em: string;
}

export interface Dashboard {
  periodo: PeriodoResolvido;
  kpis: Record<NomeKpi, Kpi>;
  series: Record<NomeKpi, PontoSerie[]>;
  status_pedidos: Distribuicao[];
  formas_pagamento: Distribuicao[];
  top_produtos: TopProduto[];
  alertas: Alertas;
  minhas_tarefas: TarefaResumo[];
  proximos_eventos: EventoResumo[];
  atividades: Atividade[];
}
