import type { Situacao } from "./types";

export const ROTULO_SITUACAO: Record<Situacao, string> = { ok: "Normal", baixo: "Baixo", esgotado: "Esgotado" };

export const COR_SITUACAO: Record<Situacao, string> = {
  ok: "bg-success/15 text-success",
  baixo: "bg-warning/20 text-warning",
  esgotado: "bg-destructive/15 text-destructive",
};
