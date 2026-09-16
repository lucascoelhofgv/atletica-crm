import { QueryClient } from "@tanstack/react-query";

import { ApiErro } from "./api";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      // Erros 4xx são definitivos (permissão, validação, não encontrado);
      // só vale repetir em falha de rede/servidor.
      retry: (tentativas, erro) => {
        if (erro instanceof ApiErro && erro.status > 0 && erro.status < 500) return false;
        return tentativas < 2;
      },
    },
    mutations: { retry: false },
  },
});
