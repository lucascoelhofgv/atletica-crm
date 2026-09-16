import { Link } from "@tanstack/react-router";
import { CalendarDays, MessageSquare, Paperclip } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { dataCurta, iniciais } from "@/lib/formatos";
import { cn } from "@/lib/utils";

import { COR_PRIORIDADE } from "../prioridade";
import type { TarefaCartao } from "../types";

export function CartaoTarefa({
  tarefa,
  arrastando,
  className,
}: {
  tarefa: TarefaCartao;
  arrastando?: boolean;
  className?: string;
}) {
  const vinculo = tarefa.cliente?.nome ?? tarefa.pedido?.nome ?? tarefa.fornecedor?.nome;
  return (
    <div
      className={cn(
        "rounded-lg border bg-card p-3 text-sm shadow-xs transition-shadow",
        arrastando ? "shadow-lg ring-2 ring-primary/40" : "hover:shadow-md",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <Link
          to="/tarefas/$id"
          params={{ id: String(tarefa.id) }}
          className="font-medium leading-snug hover:underline"
          onClick={(e) => e.stopPropagation()}
          onPointerDown={(e) => e.stopPropagation()}
        >
          {tarefa.titulo}
        </Link>
        {tarefa.prioridade !== "normal" && (
          <Badge variant="secondary" className={cn("shrink-0 font-normal", COR_PRIORIDADE[tarefa.prioridade])}>{tarefa.prioridade_rotulo}</Badge>
        )}
      </div>
      {vinculo && <div className="mt-1 truncate text-xs text-muted-foreground">{vinculo}</div>}
      <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
        {tarefa.prazo && (
          <span className={cn("flex items-center gap-1", tarefa.atrasada && "font-medium text-destructive")}>
            <CalendarDays className="size-3" /> {dataCurta(tarefa.prazo)}
          </span>
        )}
        {tarefa.qtd_comentarios > 0 && <span className="flex items-center gap-1"><MessageSquare className="size-3" /> {tarefa.qtd_comentarios}</span>}
        {tarefa.anexo && <Paperclip className="size-3" />}
        {tarefa.responsavel && (
          <Avatar className="ml-auto size-6" title={tarefa.responsavel.nome}>
            <AvatarFallback className="text-[10px]">{iniciais(tarefa.responsavel.nome)}</AvatarFallback>
          </Avatar>
        )}
      </div>
    </div>
  );
}
