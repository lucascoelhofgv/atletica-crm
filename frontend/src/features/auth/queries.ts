import { queryOptions, useQuery } from "@tanstack/react-query";

import { buscarUsuarioAtual } from "./api";
import type { Modulo, Usuario } from "./types";

export const usuarioAtualQuery = queryOptions({
  queryKey: ["auth", "me"],
  queryFn: buscarUsuarioAtual,
  staleTime: 5 * 60_000,
});

/**
 * Usuário logado. Dentro de `/_auth` o `beforeLoad` já garantiu que existe,
 * por isso o `!`; se a sessão cair, o cliente de API redireciona para o login.
 */
export function useUsuario(): Usuario {
  return useQuery(usuarioAtualQuery).data!;
}

export function usePermissao(modulo: Modulo) {
  const usuario = useUsuario();
  return usuario.permissoes[modulo] ?? { ler: false, escrever: false, excluir: false };
}
