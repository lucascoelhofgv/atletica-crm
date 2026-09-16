export interface Categoria {
  id: number;
  nome: string;
  cor: string;
  ativo?: boolean;
}

export interface Tag {
  id: number;
  nome: string;
  cor: string;
}

export interface Opcao {
  valor: string;
  rotulo: string;
}

export interface OpcoesCliente {
  categorias: Categoria[];
  tags: Tag[];
  vinculos: Opcao[];
  relacionamentos: Opcao[];
  tipos_interacao: Opcao[];
}

export interface ClienteLista {
  id: number;
  nome: string;
  nome_social: string;
  email: string;
  telefone: string;
  whatsapp: string;
  curso: string;
  periodo: string;
  membro_fgv: boolean;
  vinculo: string;
  vinculo_rotulo: string;
  categoria: Categoria | null;
  tags: Tag[];
  relacionamento: string;
  relacionamento_rotulo: string;
  qtd_pedidos: number;
  total_gasto: number;
  criado_em: string;
}

export interface Interacao {
  id: number;
  tipo: string;
  tipo_rotulo: string;
  resumo: string;
  detalhe: string;
  data: string;
  registrado_por: { id: number; nome: string } | null;
  criado_em: string;
}

export interface PedidoResumo {
  id: number;
  numero: string;
  status: string;
  status_rotulo: string;
  valor_total: number;
  data_compra: string;
  url: string;
}

export interface Cliente extends ClienteLista {
  cpf: string;
  data_nascimento: string | null;
  cidade: string;
  endereco: string;
  campus: string;
  turma: string;
  origem: string;
  aceita_comunicacoes: boolean;
  observacoes: string;
  atualizado_em: string;
  criado_por: { id: number; nome: string } | null;
  pedidos_recentes: PedidoResumo[];
  interacoes: Interacao[];
}

/** Corpo de criação/edição (o que o formulário manda). */
export interface ClienteEntrada {
  nome: string;
  nome_social: string;
  cpf: string;
  data_nascimento: string | null;
  email: string;
  telefone: string;
  whatsapp: string;
  cidade: string;
  endereco: string;
  membro_fgv: boolean;
  vinculo: string;
  curso: string;
  periodo: string;
  campus: string;
  turma: string;
  categoria_id: number | null;
  tags_ids: number[];
  origem: string;
  relacionamento: string;
  aceita_comunicacoes: boolean;
  observacoes: string;
}

export interface FiltrosClientes {
  q?: string;
  categoria?: number;
  relacionamento?: string;
  fgv?: boolean;
  tag?: number;
  pagina?: number;
  ordenar?: string;
}
