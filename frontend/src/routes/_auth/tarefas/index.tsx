import {
  DndContext, DragOverlay, PointerSensor, TouchSensor, useDraggable, useDroppable, useSensor, useSensors,
  type DragEndEvent, type DragStartEvent,
} from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { List, Plus, Search, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { z } from "zod";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { ErroCarregamento, SkeletonLinhas } from "@/components/estado";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { usePermissao, useUsuario } from "@/features/auth/queries";
import { chaves, moverTarefa, opcoesTarefaQuery, quadroQuery } from "@/features/tarefas/api";
import { CartaoTarefa } from "@/features/tarefas/components/CartaoTarefa";
import { ORDEM_COLUNAS } from "@/features/tarefas/prioridade";
import type { Coluna, StatusTarefa, TarefaCartao } from "@/features/tarefas/types";
import { numero } from "@/lib/formatos";
import { cn } from "@/lib/utils";

const buscaSchema = z.object({
  q: z.string().optional().catch(undefined),
  responsavel: z.number().optional().catch(undefined),
  minhas: z.boolean().optional().catch(undefined),
  encerradas: z.boolean().optional().catch(undefined),
});

export const Route = createFileRoute("/_auth/tarefas/")({
  validateSearch: buscaSchema,
  component: PaginaQuadro,
});

const TODOS = "__todos__";

function Cartao({ tarefa, podeArrastar }: { tarefa: TarefaCartao; podeArrastar: boolean }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: tarefa.id,
    data: { status: tarefa.status },
    disabled: !podeArrastar,
  });
  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Translate.toString(transform) }}
      {...listeners}
      {...attributes}
      className={cn("touch-none", podeArrastar && "cursor-grab active:cursor-grabbing", isDragging && "opacity-40")}
    >
      <CartaoTarefa tarefa={tarefa} />
    </div>
  );
}

function ColunaQuadro({ coluna, podeArrastar }: { coluna: Coluna; podeArrastar: boolean }) {
  const { setNodeRef, isOver } = useDroppable({ id: coluna.status });
  const encerrada = coluna.status === "concluida" || coluna.status === "cancelada";
  return (
    <div
      ref={setNodeRef}
      className={cn(
        "flex w-64 min-w-56 flex-1 shrink-0 flex-col rounded-xl border bg-muted/30 transition-colors xl:w-auto",
        isOver && "border-primary/50 bg-primary/5",
        encerrada && "opacity-90",
      )}
    >
      <div className="flex items-center justify-between px-3 py-2.5">
        <span className="text-sm font-medium">{coluna.rotulo}</span>
        <span className="tabular rounded-full bg-muted px-2 text-xs text-muted-foreground">{numero(coluna.tarefas.length)}</span>
      </div>
      <div className="scroll-suave flex max-h-[70vh] flex-1 flex-col gap-2 overflow-y-auto px-2 pb-2">
        {coluna.tarefas.map((t) => <Cartao key={t.id} tarefa={t} podeArrastar={podeArrastar} />)}
        {coluna.tarefas.length === 0 && (
          <div className="rounded-lg border border-dashed px-3 py-6 text-center text-xs text-muted-foreground">
            {isOver ? "solte aqui" : encerrada ? "arraste para cá ao encerrar" : "nada por aqui"}
          </div>
        )}
      </div>
    </div>
  );
}

function PaginaQuadro() {
  const filtros = Route.useSearch();
  const navigate = Route.useNavigate();
  const usuario = useUsuario();
  const permissao = usePermissao("tarefas");
  const queryClient = useQueryClient();
  const filtrosApi = useMemo(() => ({
    q: filtros.q, responsavel: filtros.responsavel, minhas: filtros.minhas, abertas: filtros.encerradas ? undefined : true,
  }), [filtros]);
  const consulta = useQuery(quadroQuery(filtrosApi));
  const { data: opcoes } = useQuery(opcoesTarefaQuery);
  const [arrastando, setArrastando] = useState<TarefaCartao | null>(null);
  const sensores = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 150, tolerance: 6 } }),
  );

  const [termo, setTermo] = useState(filtros.q ?? "");
  useEffect(() => {
    const t = window.setTimeout(() => {
      if ((filtros.q ?? "") !== termo) definir({ q: termo || undefined });
    }, 300);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [termo]);
  function definir(patch: Partial<typeof filtros>) {
    void navigate({ search: (ant) => ({ ...ant, ...patch }), replace: true });
  }

  const mover = useMutation({
    mutationFn: ({ id, status }: { id: number; status: StatusTarefa }) => moverTarefa(id, status),
    onMutate: async ({ id, status }) => {
      const chave = chaves.quadro(filtrosApi);
      await queryClient.cancelQueries({ queryKey: chave });
      const anterior = queryClient.getQueryData<{ colunas: Coluna[] }>(chave);
      if (anterior) {
        let movida: TarefaCartao | undefined;
        const colunas = anterior.colunas.map((c) => {
          const resto = c.tarefas.filter((t) => t.id !== id || ((movida = t), false));
          return { ...c, tarefas: resto };
        });
        if (movida) {
          const alvo = colunas.find((c) => c.status === status);
          alvo?.tarefas.unshift({ ...movida, status });
        }
        queryClient.setQueryData(chave, { colunas });
      }
      return { anterior, chave };
    },
    onError: (erro: Error, _v, ctx) => {
      if (ctx?.anterior) queryClient.setQueryData(ctx.chave, ctx.anterior);
      toast.error(erro.message);
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: chaves.todos });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  function aoIniciar(e: DragStartEvent) {
    const t = consulta.data?.colunas.flatMap((c) => c.tarefas).find((x) => x.id === e.active.id);
    setArrastando(t ?? null);
  }
  function aoSoltar(e: DragEndEvent) {
    setArrastando(null);
    const destino = e.over?.id as StatusTarefa | undefined;
    const origem = e.active.data.current?.status as StatusTarefa | undefined;
    if (!destino || destino === origem) return;
    mover.mutate({ id: Number(e.active.id), status: destino });
  }

  const colunas = consulta.data
    ? ORDEM_COLUNAS.map((s) => consulta.data!.colunas.find((c) => c.status === s)).filter((c): c is Coluna => !!c)
    : [];

  return (
    <div className="space-y-4">
      <CabecalhoPagina
        titulo="Tarefas"
        descricao="Arraste os cartões entre as colunas para mudar o status."
        acoes={
          <>
            <Button asChild variant="outline" size="sm"><Link to="/tarefas/lista" search={{}}><List /> Lista</Link></Button>
            {permissao.escrever && <Button asChild size="sm"><Link to="/tarefas/nova"><Plus /> Nova tarefa</Link></Button>}
          </>
        }
      >
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative w-full max-w-xs">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input placeholder="Título ou descrição…" className="h-8 pl-8 pr-8" value={termo} onChange={(e) => setTermo(e.target.value)} />
            {termo && <button type="button" onClick={() => setTermo("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground" aria-label="Limpar busca"><X className="size-4" /></button>}
          </div>
          <Select value={filtros.responsavel ? String(filtros.responsavel) : TODOS} onValueChange={(v) => definir({ responsavel: v === TODOS ? undefined : Number(v), minhas: undefined })}>
            <SelectTrigger size="sm" className="w-48"><SelectValue placeholder="Responsável" /></SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Qualquer responsável</SelectItem>
              {opcoes?.membros.map((m) => <SelectItem key={m.id} value={String(m.id)}>{m.nome}</SelectItem>)}
            </SelectContent>
          </Select>
          <div className="flex items-center gap-2">
            <Switch id="minhas" checked={!!filtros.minhas} onCheckedChange={(v) => definir({ minhas: v || undefined, responsavel: undefined })} />
            <Label htmlFor="minhas" className="cursor-pointer text-xs font-normal text-muted-foreground">Só as minhas</Label>
          </div>
          <div className="flex items-center gap-2">
            <Switch id="encerradas" checked={!!filtros.encerradas} onCheckedChange={(v) => definir({ encerradas: v || undefined })} />
            <Label htmlFor="encerradas" className="cursor-pointer text-xs font-normal text-muted-foreground">Mostrar encerradas</Label>
          </div>
        </div>
      </CabecalhoPagina>

      {consulta.isError && !consulta.data ? (
        <ErroCarregamento erro={consulta.error} tentarDeNovo={() => consulta.refetch()} />
      ) : !consulta.data ? (
        <SkeletonLinhas n={6} />
      ) : (
        <DndContext sensors={sensores} onDragStart={aoIniciar} onDragEnd={aoSoltar} onDragCancel={() => setArrastando(null)}>
          <div className={cn("scroll-suave flex gap-3 overflow-x-auto pb-2 transition-opacity", consulta.isFetching && "opacity-80")}>
            {colunas.map((c) => <ColunaQuadro key={c.status} coluna={c} podeArrastar={permissao.escrever} />)}
          </div>
          <DragOverlay dropAnimation={null}>
            {arrastando && <div className="w-72"><CartaoTarefa tarefa={arrastando} arrastando /></div>}
          </DragOverlay>
        </DndContext>
      )}
      {!usuario.permissoes.tarefas.escrever && <p className="text-xs text-muted-foreground">Seu perfil só visualiza.</p>}
    </div>
  );
}
