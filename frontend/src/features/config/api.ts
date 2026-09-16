import { queryOptions } from "@tanstack/react-query";

import { api } from "@/lib/api";

export interface Configuracao {
  nome_organizacao: string;
  titulo_app: string;
  sobre: string;
  logo: string | null;
  favicon: string | null;
  banner: string | null;
  cor_primaria: string;
  cor_secundaria: string;
  modo_escuro_disponivel: boolean;
  email_contato: string;
  telefone_contato: string;
  site: string;
  instagram: string;
  endereco: string;
  atualizado_em: string;
}

export const configQuery = queryOptions({
  queryKey: ["config"],
  queryFn: () => api<Configuracao>("config/"),
  staleTime: 10 * 60_000,
});

export function atualizarConfig(dados: FormData | Partial<Configuracao>) {
  return api<Configuracao>("config/", { method: "PATCH", body: dados });
}
