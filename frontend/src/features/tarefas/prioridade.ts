import type { Prioridade, StatusTarefa } from "./types";

export const COR_PRIORIDADE: Record<Prioridade, string> = {
  urgente: "bg-destructive/15 text-destructive",
  alta: "bg-warning/20 text-warning",
  normal: "bg-muted text-muted-foreground",
  baixa: "bg-muted text-muted-foreground/70",
};

export const COR_STATUS: Record<StatusTarefa, string> = {
  a_fazer: "bg-muted text-muted-foreground",
  em_andamento: "bg-primary/15 text-primary",
  aguardando: "bg-warning/20 text-warning",
  concluida: "bg-success/15 text-success",
  cancelada: "bg-destructive/10 text-destructive",
};

export const ORDEM_COLUNAS: StatusTarefa[] = ["a_fazer", "em_andamento", "aguardando", "concluida", "cancelada"];
