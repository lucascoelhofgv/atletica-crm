import { keepPreviousData, queryOptions } from "@tanstack/react-query";

import { api, type Paginado } from "@/lib/api";

export interface Membro {
  id: number;
  username: string;
  nome: string;
  first_name: string;
  last_name: string;
  email: string;
  cargo: string;
  telefone: string;
  foto: string | null;
  data_entrada: string | null;
  data_saida: string | null;
  observacoes: string;
  is_active: boolean;
  is_superuser: boolean;
  last_login: string | null;
  date_joined: string;
  perfis: string[];
  perfil_principal: string;
}

export interface MembroEntrada {
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  cargo: string;
  telefone: string;
  data_entrada: string | null;
  data_saida: string | null;
  observacoes: string;
  is_active: boolean;
  grupos_ids: number[];
  senha?: string;
}

export interface FiltrosMembros {
  q?: string;
  is_active?: boolean;
  pagina?: number;
}

export const chaves = {
  todos: ["membros"] as const,
  lista: (f: FiltrosMembros) => ["membros", "lista", f] as const,
  opcoes: ["membros", "opcoes"] as const,
};

export const membrosQuery = (f: FiltrosMembros) =>
  queryOptions({
    queryKey: chaves.lista(f),
    queryFn: () => api<Paginado<Membro>>("membros/", { params: { ...f, tamanho: 100 } }),
    placeholderData: keepPreviousData,
  });

export const opcoesMembroQuery = queryOptions({
  queryKey: chaves.opcoes,
  queryFn: () => api<{ grupos: { id: number; name: string }[]; perfis_ordem: string[] }>("membros/opcoes/"),
  staleTime: 10 * 60_000,
});

export const criarMembro = (d: MembroEntrada) => api<Membro>("membros/", { method: "POST", body: d });
export const atualizarMembro = (id: number, d: Partial<MembroEntrada>) => api<Membro>(`membros/${id}/`, { method: "PATCH", body: d });
export const alternarMembro = (id: number) => api<Membro>(`membros/${id}/alternar/`, { method: "POST" });

/* Atividades e acessos (histórico) */
export interface Atividade {
  id: number;
  usuario: { id: number; nome: string } | null;
  verbo: string;
  alvo: string;
  descricao: string;
  url: string;
  criado_em: string;
}
export interface Acesso {
  id: number;
  usuario: { id: number; nome: string } | null;
  momento: string;
  ip: string | null;
  agente: string;
  sucesso: boolean;
}
export const atividadesQuery = (f: { q?: string; pagina?: number }) =>
  queryOptions({
    queryKey: ["atividades", f],
    queryFn: () => api<Paginado<Atividade>>("atividades/", { params: { ...f, tamanho: 50 } }),
    placeholderData: keepPreviousData,
  });
export const acessosQuery = (f: { pagina?: number }) =>
  queryOptions({
    queryKey: ["acessos", f],
    queryFn: () => api<Paginado<Acesso>>("acessos/", { params: { ...f, tamanho: 50 } }),
    placeholderData: keepPreviousData,
  });
