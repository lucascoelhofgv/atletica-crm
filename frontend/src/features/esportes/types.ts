export type Naipe = "masc" | "fem" | "misto";

export interface LinhaModalidade {
  id: number;
  nome: string;
  esporte: string;
  naipe: Naipe;
  local: string;
  dia_semana: string;
  tem_orcamento: boolean;
  tem_registros: boolean;
  orcado: number;
  realizado: number;
  diferenca: number;
  /** realizado / orçado, em fração; null sem orçamento. */
  uso: number | null;
  realizado_tecnico: number;
  realizado_quadra: number;
  treinos_previstos: number;
  treinos_registrados: number;
  treinos_confirmados: number;
  treinos_cancelados: number;
  jogos_previstos: number;
  jogos_registrados: number;
  valor_quadra_orcado: number | null;
  valor_quadra_real: number | null;
  valor_tecnico_orcado: number | null;
  valor_tecnico_real: number | null;
}

export interface MesEsportes {
  mes: string; // "2026-03"
  realizado: number;
  tecnico: number;
  quadra: number;
  treinos: number;
  jogos: number;
}

export interface ResumoEsportes {
  ano: number;
  semestre: 1 | 2;
  semestres_disponiveis: { ano: number; semestre: 1 | 2 }[];
  ultima_sincronizacao: string | null;
  primeiro_registro: string | null;
  ultimo_registro: string | null;
  totais: {
    orcado: number;
    realizado: number;
    diferenca: number;
    uso: number | null;
    treinos_previstos: number;
    treinos_registrados: number;
    treinos_confirmados: number;
    treinos_cancelados: number;
    jogos_previstos: number;
    jogos_registrados: number;
  };
  modalidades: LinhaModalidade[];
  por_mes: MesEsportes[];
}

export interface FontePlanilha {
  id: number;
  nome: string;
  planilha: string;
  aba: string;
  destino: string;
  destino_rotulo: string;
  modo: string;
  ativa: boolean;
  ultima_sincronizacao: string | null;
  ultimo_resultado: string;
  ultimo_erro: string;
  criado_em: string;
  criado_por_nome: string;
}

export interface OpcoesFontes {
  destinos: { valor: string; rotulo: string }[];
  modos: { valor: string; rotulo: string }[];
  conta_servico: string;
}

export interface ResultadoSincronizacao {
  resumo: string;
  avisos: string[];
  fonte: FontePlanilha;
}
