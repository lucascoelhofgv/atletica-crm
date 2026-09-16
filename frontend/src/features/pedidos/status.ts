import type { StatusPedido } from "./types";

export const COR_STATUS: Record<StatusPedido, string> = {
  rascunho: "bg-muted text-muted-foreground",
  aguardando_pagamento: "bg-warning/20 text-warning",
  pago: "bg-success/15 text-success",
  em_separacao: "bg-primary/15 text-primary",
  pronto: "bg-primary/15 text-primary",
  entregue: "bg-success/15 text-success",
  cancelado: "bg-destructive/10 text-destructive",
  devolvido: "bg-destructive/10 text-destructive",
};

export const COR_PAGAMENTO: Record<string, string> = {
  pendente: "bg-warning/20 text-warning",
  parcial: "bg-primary/15 text-primary",
  quitado: "bg-success/15 text-success",
};

/** Status que baixam estoque ao serem atingidos. */
export const STATUS_BAIXA = new Set<StatusPedido>(["pago", "em_separacao", "pronto", "entregue"]);

/** Fluxo sugerido (próximo passo natural) para o botão de avanço. */
export const PROXIMO_STATUS: Partial<Record<StatusPedido, StatusPedido>> = {
  rascunho: "aguardando_pagamento",
  aguardando_pagamento: "pago",
  pago: "em_separacao",
  em_separacao: "pronto",
  pronto: "entregue",
};
