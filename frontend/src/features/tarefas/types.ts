import type { Opcao } from "@/features/clientes/types";

export type StatusTarefa = "a_fazer" | "em_andamento" | "aguardando" | "concluida" | "cancelada";
export type Prioridade = "baixa" | "normal" | "alta" | "urgente";

export interface Vinculo {
  id: number;
  nome: string;
}

export interface Comentario {
  id: number;
  texto: string;
  autor: { id: number; nome: string } | null;
  criado_em: string;
}

export interface TarefaCartao {
  id: number;
  titulo: string;
  descricao: string;
  responsavel: { id: number; nome: string } | null;
  criador: { id: number; nome: string } | null;
  prazo: string | null;
  prioridade: Prioridade;
  prioridade_rotulo: string;
  status: StatusTarefa;
  status_rotulo: string;
  atrasada: boolean;
  cliente: Vinculo | null;
  pedido: Vinculo | null;
  fornecedor: Vinculo | null;
  anexo: string | null;
  criado_em: string;
  atualizado_em: string;
  concluida_em: string | null;
  qtd_comentarios: number;
}

export interface Tarefa extends TarefaCartao {
  comentarios: Comentario[];
}

export interface TarefaEntrada {
  titulo: string;
  descricao: string;
  responsavel_id: number | null;
  prazo: string | null;
  prioridade: Prioridade;
  status: StatusTarefa;
  cliente_id: number | null;
  pedido_id: number | null;
  fornecedor_id: number | null;
}

export interface Coluna {
  status: StatusTarefa;
  rotulo: string;
  tarefas: TarefaCartao[];
}

export interface OpcoesTarefa {
  status: Opcao[];
  prioridades: Opcao[];
  membros: { id: number; nome: string }[];
}

export interface FiltrosTarefas {
  q?: string;
  status?: string;
  prioridade?: string;
  responsavel?: number;
  minhas?: boolean;
  atrasadas?: boolean;
  abertas?: boolean;
  pagina?: number;
}
