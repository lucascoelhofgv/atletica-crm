import { useMutation, useQuery, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { CalendarDays, Check, LoaderCircle, Paperclip, Pencil, Send, Trash2, UserRound } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { ConfirmarExclusao } from "@/components/ConfirmarExclusao";
import { PaginaCarregando } from "@/components/estado";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { usePermissao, useUsuario } from "@/features/auth/queries";
import {
  chaves, comentarTarefa, enviarAnexo, excluirComentario, excluirTarefa, moverTarefa, opcoesTarefaQuery, tarefaQuery,
} from "@/features/tarefas/api";
import { COR_PRIORIDADE, COR_STATUS } from "@/features/tarefas/prioridade";
import type { StatusTarefa, Tarefa } from "@/features/tarefas/types";
import { data as fmtData, dataHora, relativo } from "@/lib/formatos";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_auth/tarefas/$id/")({
  loader: ({ context, params }) => context.queryClient.ensureQueryData(tarefaQuery(Number(params.id))),
  pendingComponent: PaginaCarregando,
  component: PaginaTarefa,
});

function PaginaTarefa() {
  const { id } = Route.useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const permissao = usePermissao("tarefas");
  const usuario = useUsuario();
  const { data: t } = useSuspenseQuery(tarefaQuery(Number(id)));
  const { data: opcoes } = useQuery(opcoesTarefaQuery);
  const [texto, setTexto] = useState("");

  function atualizar(nova: Tarefa) {
    queryClient.setQueryData(chaves.detalhe(nova.id), nova);
    void queryClient.invalidateQueries({ queryKey: chaves.todos });
    void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  }
  const mover = useMutation({ mutationFn: (s: StatusTarefa) => moverTarefa(t.id, s), onSuccess: (n) => { atualizar(n); toast.success(`Tarefa: ${n.status_rotulo}.`); }, onError: (e: Error) => toast.error(e.message) });
  const comentar = useMutation({ mutationFn: () => comentarTarefa(t.id, texto.trim()), onSuccess: (n) => { atualizar(n); setTexto(""); }, onError: (e: Error) => toast.error(e.message) });
  const apagarComentario = useMutation({ mutationFn: (cid: number) => excluirComentario(t.id, cid), onSuccess: atualizar, onError: (e: Error) => toast.error(e.message) });
  const anexo = useMutation({ mutationFn: (a: File | null) => enviarAnexo(t.id, a), onSuccess: (n) => { atualizar(n); toast.success("Anexo atualizado."); }, onError: (e: Error) => toast.error(e.message) });
  const excluir = useMutation({
    mutationFn: () => excluirTarefa(t.id),
    onSuccess: () => { void queryClient.invalidateQueries({ queryKey: chaves.todos }); toast.success("Tarefa excluída."); void router.navigate({ to: "/tarefas", search: {} }); },
    onError: (e: Error) => toast.error(e.message),
  });
  const encerrada = t.status === "concluida" || t.status === "cancelada";

  return (
    <div className="space-y-6">
      <CabecalhoPagina
        titulo={t.titulo}
        voltar={{ para: "/tarefas", rotulo: "Tarefas" }}
        descricao={
          <span className="flex flex-wrap items-center gap-1.5">
            <Badge variant="secondary" className={cn("font-normal", COR_STATUS[t.status])}>{t.status_rotulo}</Badge>
            <Badge variant="secondary" className={cn("font-normal", COR_PRIORIDADE[t.prioridade])}>{t.prioridade_rotulo}</Badge>
            {t.prazo && <span className={cn("flex items-center gap-1 text-xs", t.atrasada ? "font-medium text-destructive" : "text-muted-foreground")}><CalendarDays className="size-3.5" /> {t.atrasada ? "atrasada · " : ""}{fmtData(t.prazo)}</span>}
            {t.responsavel && <span className="flex items-center gap-1 text-xs text-muted-foreground"><UserRound className="size-3.5" /> {t.responsavel.nome}</span>}
          </span>
        }
        acoes={
          permissao.escrever ? (
            <>
              {!encerrada && (
                <Button size="sm" onClick={() => mover.mutate("concluida")} disabled={mover.isPending}>
                  {mover.isPending ? <LoaderCircle className="animate-spin" /> : <Check />} Concluir
                </Button>
              )}
              <Button asChild size="sm" variant="outline"><Link to="/tarefas/$id/editar" params={{ id }}><Pencil /> Editar</Link></Button>
              {permissao.excluir && <ConfirmarExclusao titulo="Excluir tarefa?" descricao="Comentários e anexo somem junto." aoConfirmar={() => excluir.mutateAsync()} pendente={excluir.isPending} />}
            </>
          ) : undefined
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <CardTitle>Descrição</CardTitle>
              {permissao.escrever && (
                <Select value={t.status} onValueChange={(v) => mover.mutate(v as StatusTarefa)} disabled={mover.isPending}>
                  <SelectTrigger size="sm" className="w-44"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {opcoes?.status.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
                  </SelectContent>
                </Select>
              )}
            </CardHeader>
            <CardContent>
              {t.descricao ? <p className="whitespace-pre-line text-sm">{t.descricao}</p> : <p className="text-sm text-muted-foreground">Sem descrição.</p>}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Comentários</CardTitle>
              <CardDescription>{t.comentarios.length === 0 ? "Ninguém comentou ainda" : `${t.comentarios.length} ${t.comentarios.length === 1 ? "comentário" : "comentários"}`}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {t.comentarios.length > 0 && (
                <ol className="space-y-3">
                  {t.comentarios.map((c) => (
                    <li key={c.id} className="group rounded-lg bg-muted/40 p-3 text-sm">
                      <div className="flex items-start justify-between gap-2">
                        <span className="font-medium">{c.autor?.nome ?? "—"}</span>
                        <span className="flex items-center gap-2 text-[11px] text-muted-foreground" title={dataHora(c.criado_em)}>
                          {relativo(c.criado_em)}
                          {(usuario.eh_admin || c.autor?.id === usuario.id) && (
                            <button type="button" onClick={() => apagarComentario.mutate(c.id)} className="opacity-0 hover:text-destructive group-hover:opacity-100 pointer-coarse:opacity-100" aria-label="Excluir comentário"><Trash2 className="size-3.5" /></button>
                          )}
                        </span>
                      </div>
                      <p className="mt-1 whitespace-pre-line">{c.texto}</p>
                    </li>
                  ))}
                </ol>
              )}
              {permissao.escrever && (
                <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); if (texto.trim()) comentar.mutate(); }}>
                  <Textarea rows={2} placeholder="Escreva um comentário…" value={texto} onChange={(e) => setTexto(e.target.value)}
                    onKeyDown={(e) => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter" && texto.trim()) comentar.mutate(); }} />
                  <Button type="submit" size="icon" disabled={!texto.trim() || comentar.isPending} aria-label="Enviar">
                    {comentar.isPending ? <LoaderCircle className="animate-spin" /> : <Send />}
                  </Button>
                </form>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Vínculos</CardTitle></CardHeader>
            <CardContent className="space-y-2 text-sm">
              {t.cliente && <div><span className="text-xs text-muted-foreground">Cliente</span><div><Link to="/clientes/$id" params={{ id: String(t.cliente.id) }} className="hover:underline">{t.cliente.nome}</Link></div></div>}
              {t.pedido && <div><span className="text-xs text-muted-foreground">Pedido</span><div><Link to="/pedidos/$id" params={{ id: String(t.pedido.id) }} className="hover:underline">{t.pedido.nome}</Link></div></div>}
              {t.fornecedor && <div><span className="text-xs text-muted-foreground">Fornecedor</span><div><Link to="/fornecedores/$id" params={{ id: String(t.fornecedor.id) }} className="hover:underline">{t.fornecedor.nome}</Link></div></div>}
              {!t.cliente && !t.pedido && !t.fornecedor && <p className="text-muted-foreground">Sem vínculos.</p>}
              <div className="flex items-center gap-2 border-t pt-3 text-xs">
                <Paperclip className="size-3.5 text-muted-foreground" />
                {t.anexo ? <a href={t.anexo} target="_blank" rel="noreferrer" className="hover:underline">ver anexo</a> : <span className="text-muted-foreground">sem anexo</span>}
                {permissao.escrever && (
                  <label className="ml-auto cursor-pointer text-muted-foreground hover:text-foreground">
                    {anexo.isPending ? "enviando…" : t.anexo ? "trocar" : "anexar"}
                    <input type="file" className="hidden" onChange={(e) => e.target.files?.[0] && anexo.mutate(e.target.files[0])} />
                  </label>
                )}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Histórico</CardTitle></CardHeader>
            <CardContent className="space-y-1 text-xs text-muted-foreground">
              <div>Criada {relativo(t.criado_em)}{t.criador && ` por ${t.criador.nome}`}</div>
              <div>Atualizada {relativo(t.atualizado_em)}</div>
              {t.concluida_em && <div className="text-success">Concluída em {dataHora(t.concluida_em)}</div>}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
