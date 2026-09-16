import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { LoaderCircle, Mail, MapPin, MessageCircle, Pencil, Phone, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";
import { ConfirmarExclusao } from "@/components/ConfirmarExclusao";
import { PaginaCarregando, Vazio } from "@/components/estado";
import { aplicarErrosApi, Campo } from "@/components/formulario";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { usePermissao } from "@/features/auth/queries";
import {
  chaves, clienteQuery, excluirCliente, excluirInteracao, opcoesClienteQuery, registrarInteracao,
} from "@/features/clientes/api";
import type { Cliente } from "@/features/clientes/types";
import { data as fmtData, dataHora, moeda, numero, relativo } from "@/lib/formatos";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_auth/clientes/$id/")({
  loader: ({ context, params }) => context.queryClient.ensureQueryData(clienteQuery(Number(params.id))),
  pendingComponent: PaginaCarregando,
  component: PaginaCliente,
});

const COR_STATUS_PEDIDO: Record<string, string> = {
  pago: "bg-success/15 text-success",
  entregue: "bg-success/15 text-success",
  em_separacao: "bg-primary/15 text-primary",
  pronto: "bg-primary/15 text-primary",
  aguardando_pagamento: "bg-warning/20 text-warning",
  cancelado: "bg-destructive/10 text-destructive",
  devolvido: "bg-destructive/10 text-destructive",
};

function Linha({ icone: Icone, valor, href }: { icone: typeof Mail; valor: string; href?: string }) {
  if (!valor) return null;
  const conteudo = (
    <span className="flex items-center gap-2 text-sm">
      <Icone className="size-4 shrink-0 text-muted-foreground" /> {valor}
    </span>
  );
  return href ? <a href={href} target="_blank" rel="noreferrer" className="hover:underline">{conteudo}</a> : conteudo;
}

function Dado({ rotulo, valor }: { rotulo: string; valor?: string | null }) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wide text-muted-foreground">{rotulo}</div>
      <div className="text-sm">{valor || "—"}</div>
    </div>
  );
}

const esquemaInteracao = z.object({
  tipo: z.string().min(1, "Escolha o tipo"),
  resumo: z.string().trim().min(3, "Descreva em poucas palavras"),
  detalhe: z.string(),
});

function NovaInteracao({ cliente }: { cliente: Cliente }) {
  const [aberto, setAberto] = useState(false);
  const queryClient = useQueryClient();
  const { data: opcoes } = useQuery(opcoesClienteQuery);
  const form = useForm<z.infer<typeof esquemaInteracao>>({
    resolver: zodResolver(esquemaInteracao),
    defaultValues: { tipo: "whatsapp", resumo: "", detalhe: "" },
  });
  const registrar = useMutation({
    mutationFn: (d: z.infer<typeof esquemaInteracao>) => registrarInteracao(cliente.id, d),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: chaves.detalhe(cliente.id) });
      toast.success("Interação registrada.");
      form.reset();
      setAberto(false);
    },
    onError: (erro) => aplicarErrosApi(form, erro),
  });
  const erros = form.formState.errors;

  return (
    <Dialog open={aberto} onOpenChange={setAberto}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline"><Plus /> Registrar</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Nova interação</DialogTitle>
          <DialogDescription>Ligação, mensagem, conversa presencial… o que aconteceu com {cliente.nome_social || cliente.nome}.</DialogDescription>
        </DialogHeader>
        <form className="space-y-4" noValidate onSubmit={form.handleSubmit((d) => registrar.mutate(d))}>
          <Campo id="tipo" rotulo="Tipo" obrigatorio erro={erros.tipo?.message}>
            <Controller
              control={form.control}
              name="tipo"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger id="tipo" className="w-full"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {opcoes?.tipos_interacao.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
                  </SelectContent>
                </Select>
              )}
            />
          </Campo>
          <Campo id="resumo" rotulo="Resumo" obrigatorio erro={erros.resumo?.message}>
            <Input id="resumo" autoFocus {...form.register("resumo")} aria-invalid={!!erros.resumo} />
          </Campo>
          <Campo id="detalhe" rotulo="Detalhe" erro={erros.detalhe?.message}>
            <Textarea id="detalhe" rows={3} {...form.register("detalhe")} />
          </Campo>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" onClick={() => setAberto(false)}>Cancelar</Button>
            <Button type="submit" disabled={registrar.isPending}>
              {registrar.isPending && <LoaderCircle className="animate-spin" />} Salvar
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function PaginaCliente() {
  const { id } = Route.useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const permissao = usePermissao("crm");
  const { data: c } = useSuspenseQuery(clienteQuery(Number(id)));

  const excluir = useMutation({
    mutationFn: () => excluirCliente(c.id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: chaves.todos });
      toast.success("Cliente excluído.");
      void router.navigate({ to: "/clientes" });
    },
    onError: (erro: Error) => toast.error(erro.message),
  });
  const apagarInteracao = useMutation({
    mutationFn: (iid: number) => excluirInteracao(c.id, iid),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: chaves.detalhe(c.id) }),
    onError: (erro: Error) => toast.error(erro.message),
  });

  const nome = c.nome_social || c.nome;
  const whats = c.whatsapp.replace(/\D/g, "");

  return (
    <div className="space-y-6">
      <CabecalhoPagina
        titulo={nome}
        voltar={{ para: "/clientes", rotulo: "Clientes" }}
        descricao={
          <span className="flex flex-wrap items-center gap-1.5">
            {c.categoria && <Badge variant="secondary" className="font-normal">{c.categoria.nome}</Badge>}
            <Badge variant="outline" className="font-normal">{c.relacionamento_rotulo}</Badge>
            {c.vinculo_rotulo !== c.categoria?.nome && <Badge variant="outline" className="font-normal">{c.vinculo_rotulo}</Badge>}
            {c.tags.map((t) => (
              <span key={t.id} className="rounded-full px-2 py-0.5 text-[11px] text-white" style={{ background: t.cor }}>{t.nome}</span>
            ))}
          </span>
        }
        acoes={
          permissao.escrever ? (
            <>
              <Button asChild size="sm" variant="outline">
                <Link to="/clientes/$id/editar" params={{ id }}><Pencil /> Editar</Link>
              </Button>
              {permissao.excluir && (
                <ConfirmarExclusao
                  titulo={`Excluir ${nome}?`}
                  descricao="Os pedidos ficam no histórico, mas o cadastro e as interações somem. Prefira marcar como inativo se houver dúvida."
                  aoConfirmar={() => excluir.mutateAsync()}
                  pendente={excluir.isPending}
                />
              )}
            </>
          ) : undefined
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader><CardTitle>Contato</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            <Linha icone={Mail} valor={c.email} href={c.email ? `mailto:${c.email}` : undefined} />
            <Linha icone={MessageCircle} valor={c.whatsapp} href={whats ? `https://wa.me/55${whats}` : undefined} />
            <Linha icone={Phone} valor={c.telefone} />
            <Linha icone={MapPin} valor={[c.endereco, c.cidade].filter(Boolean).join(" · ")} />
            {!c.email && !c.whatsapp && !c.telefone && <p className="text-sm text-muted-foreground">Sem contato cadastrado.</p>}
            <p className="pt-2 text-xs text-muted-foreground">
              {c.aceita_comunicacoes ? "Autoriza comunicações (LGPD)." : "Não autorizou comunicações."}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Vínculo e origem</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-2 gap-3">
            <Dado rotulo="Curso" valor={c.curso} />
            <Dado rotulo="Período" valor={c.periodo} />
            <Dado rotulo="Campus" valor={c.campus} />
            <Dado rotulo="Turma" valor={c.turma} />
            <Dado rotulo="Origem" valor={c.origem} />
            <Dado rotulo="Nascimento" valor={c.data_nascimento ? fmtData(c.data_nascimento) : ""} />
            <Dado rotulo="CPF" valor={c.cpf} />
            <Dado rotulo="Cadastro" valor={`${fmtData(c.criado_em)}${c.criado_por ? ` · ${c.criado_por.nome}` : ""}`} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Compras</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-2 gap-3">
            <div>
              <div className="text-[11px] uppercase tracking-wide text-muted-foreground">Pedidos válidos</div>
              <div className="tabular font-display text-2xl font-semibold">{numero(c.qtd_pedidos)}</div>
            </div>
            <div>
              <div className="text-[11px] uppercase tracking-wide text-muted-foreground">Total gasto</div>
              <div className="tabular font-display text-2xl font-semibold">{moeda(c.total_gasto)}</div>
            </div>
            {c.observacoes && (
              <div className="col-span-2">
                <div className="text-[11px] uppercase tracking-wide text-muted-foreground">Observações</div>
                <p className="whitespace-pre-line text-sm">{c.observacoes}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <div>
              <CardTitle>Pedidos recentes</CardTitle>
              <CardDescription>Últimos 10</CardDescription>
            </div>
            <a href={`/pedidos/?q=${encodeURIComponent(c.nome)}`} className="text-xs text-muted-foreground hover:text-foreground">ver todos</a>
          </CardHeader>
          <CardContent>
            {c.pedidos_recentes.length === 0 ? (
              <Vazio titulo="Nenhum pedido ainda" className="py-8" />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Pedido</TableHead>
                    <TableHead>Data</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Valor</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {c.pedidos_recentes.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell><a href={p.url} className="font-medium hover:underline">{p.numero || `#${p.id}`}</a></TableCell>
                      <TableCell className="text-muted-foreground">{fmtData(p.data_compra)}</TableCell>
                      <TableCell><Badge variant="secondary" className={cn("font-normal", COR_STATUS_PEDIDO[p.status])}>{p.status_rotulo}</Badge></TableCell>
                      <TableCell className="tabular text-right">{moeda(p.valor_total)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <div>
              <CardTitle>Interações</CardTitle>
              <CardDescription>Histórico de contato</CardDescription>
            </div>
            {permissao.escrever && <NovaInteracao cliente={c} />}
          </CardHeader>
          <CardContent>
            {c.interacoes.length === 0 ? (
              <Vazio titulo="Nenhuma interação registrada" className="py-8" />
            ) : (
              <ol className="space-y-3">
                {c.interacoes.map((i) => (
                  <li key={i.id} className="group flex gap-3">
                    <span className="mt-1.5 size-2 shrink-0 rounded-full bg-primary/70" />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <div className="text-sm">
                          <span className="font-medium">{i.tipo_rotulo}</span> · {i.resumo}
                        </div>
                        {permissao.escrever && (
                          <button
                            type="button"
                            onClick={() => apagarInteracao.mutate(i.id)}
                            className="text-muted-foreground opacity-0 transition-opacity hover:text-destructive group-hover:opacity-100 pointer-coarse:opacity-100"
                            aria-label="Excluir interação"
                          >
                            <Trash2 className="size-3.5" />
                          </button>
                        )}
                      </div>
                      {i.detalhe && <p className="whitespace-pre-line text-xs text-muted-foreground">{i.detalhe}</p>}
                      <div className="text-[11px] text-muted-foreground" title={dataHora(i.data)}>
                        {relativo(i.data)}{i.registrado_por && ` · ${i.registrado_por.nome}`}
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
