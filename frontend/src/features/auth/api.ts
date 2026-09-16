import { api, ApiErro } from "@/lib/api";

import type { CredenciaisLogin, TrocaSenha, Usuario } from "./types";

/** `null` quando não há sessão (401). Também garante o cookie de CSRF. */
export async function buscarUsuarioAtual(): Promise<Usuario | null> {
  try {
    return await api<Usuario>("auth/me/", { silenciar401: true });
  } catch (erro) {
    if (erro instanceof ApiErro && erro.naoAutenticado) return null;
    throw erro;
  }
}

export function login(credenciais: CredenciaisLogin) {
  return api<Usuario>("auth/login/", { method: "POST", body: credenciais });
}

export function logout() {
  return api<void>("auth/logout/", { method: "POST" });
}

export function alterarSenha(dados: TrocaSenha) {
  return api<{ ok: true }>("auth/senha/", { method: "POST", body: dados });
}
