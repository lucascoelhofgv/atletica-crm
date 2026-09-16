import type { Opcao } from "@/features/clientes/types";

export interface Avaliacao {
  id: number;
  preco: number;
  qualidade: number;
  prazo: number;
  atendimento: number;
  confiabilidade: number;
  comentario: string;
  media: number;
  autor: { id: number; nome: string } | null;
  criado_em: string;
}

export interface FornecedorLista {
  id: number;
  nome: string;
  nome_fantasia: string;
  nome_exibicao: string;
  categoria: string;
  categoria_rotulo: string;
  contato_nome: string;
  email: string;
  whatsapp: string;
  telefone: string;
  status: "ativo" | "inativo";
  status_rotulo: string;
  qtd_produtos: number;
  qtd_avaliacoes: number;
  nota_media: number | null;
  prazo_medio_entrega: string;
}

export interface Fornecedor extends FornecedorLista {
  documento: string;
  endereco: string;
  produtos_servicos: string;
  condicoes_comerciais: string;
  contrato: string | null;
  observacoes: string;
  criado_em: string;
  criado_por: { id: number; nome: string } | null;
  avaliacoes: Avaliacao[];
  produtos: { id: number; nome: string; quantidade_atual: number; preco_venda: number }[];
}

export interface FornecedorEntrada {
  nome: string;
  nome_fantasia: string;
  documento: string;
  contato_nome: string;
  email: string;
  telefone: string;
  whatsapp: string;
  endereco: string;
  categoria: string;
  produtos_servicos: string;
  condicoes_comerciais: string;
  prazo_medio_entrega: string;
  status: "ativo" | "inativo";
  observacoes: string;
}

export interface AvaliacaoEntrada {
  preco: number;
  qualidade: number;
  prazo: number;
  atendimento: number;
  confiabilidade: number;
  comentario: string;
}

export interface OpcoesFornecedor {
  categorias: Opcao[];
  status: Opcao[];
}

export interface FiltrosFornecedores {
  q?: string;
  categoria?: string;
  status?: string;
  pagina?: number;
}
