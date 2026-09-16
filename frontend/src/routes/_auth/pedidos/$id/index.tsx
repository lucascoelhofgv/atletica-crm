import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, Link, useRouter } from "@tanstack/react-router";
import { AlertTriangle, ArrowRight, FileText, LoaderCircle, Paperclip, Pencil, Plus, Trash2 } from "lucide-react";
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
import { usePermissao, useUsuario } from "@/features/auth/queries";
import {
  chaves, enviarComprovante, excluirPagamento, excluirPedido, mudarStatusPedido, opcoesPedidoQuery,
  pedidoQuery, registrarPagamento,
} from "@/features/pedidos/api";
import { COR_PAGAMENTO, COR_STATUS, PROXIMO_STATUS, STATUS_BAIXA } from "@/features/pedidos/status";
import type { Pedido, StatusPedido } from "@/features/pedidos/types";
import { ApiErro } from "@/lib/api";
import { data as fmtData, dataHora, moeda, numero } from "@/lib/formatos";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_auth/pedidos/$id/")({
  loader: ({ context, params }) => context.queryClient.ensureQueryData(pedidoQuery(Number(params.id))),
  pendingComponent: PaginaCarregando,
  component: PaginaPedido,
});

function usePodePagar() {
  const u = useUsuario();
  return u.eh_admin || u.perfis.includes("Diretoria") || u.perfis.includes("Financeiro");
}

function hojeIso() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

const esquemaPagamento = z.object({
  valor: z.number({ error: "Informe o valor" }).positive("Maior que zero"),
  forma: z.string().min(1, "Escolha a forma"),
  data: z.string().min(1, "Informe a data"),
  observacao: z.string().trim().max(255),
});

function NovoPagamento({ pedido, aoAtualizar }: { pedido: Pedido; aoAtualizar: (p: Pedido) => void }) {
  const [aberto, setAberto] = useState(false);
  const { data: opcoes } = useQuery(opcoesPedidoQuery);
  const form = useForm<z.infer<typeof esquemaPagamento>>({
    resolver: zodResolver(esquemaPagamento),
    defaultValues: { valor: Math.max(0, pedido.saldo_devedor), forma: pedido.forma_pagamento || "pix", data: hojeIso(), observacao: "" },
  });
  const registrar = useMutation({
    mutationFn: (d: z.infer<typeof esquemaPagamento>) => registrarPagamento(pedido.id, d),
    onSuccess: (p) => {
      aoAtualizar(p);
      toast.success(p.status_pagamento === "quitado" ? "Pagamento registrado. Pedido quitado." : "Pagamento registrado.");
      setAberto(false);
      form.reset({ valor: Math.max(0, p.saldo_devedor), forma: p.forma_pagamento || "pix", data: hojeIso(), observacao: "" });
    },
    onError: (erro) => aplicarErrosApi(form, erro),
  });
  const erros = form.formState.errors;
  return (
    <Dialog open={aberto} onOpenChange={setAberto}>
      <DialogTrigger asChild>
        <Button size="sm" variant="outline"><Plus /> Pagamento</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Registrar pagamento</DialogTitle>
          <DialogDescription>Saldo devedor: {moeda(pedido.saldo_devedor)}.</DialogDescription>
        </DialogHeader>
        <form className="space-y-4" noValidate onSubmit={form.handleSubmit((d) => registrar.mutate(d))}>
          <div className="grid grid-cols-2 gap-3">
            <Campo id="valor" rotulo="Valor (R$)" obrigatorio erro={erros.valor?.message}>
              <Input id="valor" type="number" step="0.01" min="0.01" autoFocus {...form.register("valor", { valueAsNumber: true })} aria-invalid={!!erros.valor} />
            </Campo>
            <Campo id="data" rotulo="Data" obrigatorio erro={erros.data?.message}>
              <Input id="data" type="date" {...form.register("data")} />
            </Campo>
          </div>
          <Campo id="forma" rotulo="Forma" obrigatorio erro={erros.forma?.message}>
            <Controller
              control={form.control}
              name="forma"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger id="forma" className="w-full"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {opcoes?.formas_pagamento.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
                  </SelectContent>
                </Select>
              )}
            />
          </Campo>
          <Campo id="observacao" rotulo="Observação" erro={erros.observacao?.message}>
            <Input id="observacao" {...form.register("observacao")} />
          </Campo>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" onClick={() => setAberto(false)}>Cancelar</Button>
            <Button type="submit" disabled={registrar.isPending}>{registrar.isPending && <LoaderCircle className="animate-spin" />} Registrar</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function MudarStatus({ pedido, aoAtualizar }: { pedido: Pedido; aoAtualizar: (p: Pedido) => void }) {
  const { data: opcoes } = useQuery(opcoesPedidoQuery);
  const mudar = useMutation({
    mutationFn: (s: StatusPedido) => mudarStatusPedido(pedido.id, s),
    onSuccess: (p) => {
      aoAtualizar(p);
      toast.success(`Pedido agora está: ${p.status_rotulo}.`);
    },
    onError: (erro) => toast.error(erro instanceof ApiErro ? erro.message : "Não foi possível mudar o status."),
  });
  const proximo = PROXIMO_STATUS[pedido.status];
  const rotuloProximo = opcoes?.status.find((o) => o.valor === proximo)?.rotulo;
  return (
    <div className="flex items-center gap-2">
      <Select value={pedido.status} onValueChange={(v) => mudar.mutate(v as StatusPedido)} disabled={mudar.isPending}>
        <SelectTrigger size="sm" className="w-52"><SelectValue /></SelectTrigger>
        <SelectContent>
          {opcoes?.status.map((o) => (
            <SelectItem key={o.valor} value={o.valor}>
              {o.rotulo}{STATUS_BAIXA.has(o.valor as StatusPedido) && !pedido.estoque_baixado ? " · baixa estoque" : ""}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {proximo && rotuloProximo && (
        <Button size="sm" onClick={() => mudar.mutate(proximo)} disabled={mudar.isPending}>
          {mudar.isPending ? <LoaderCircle className="animate-spin" /> : <ArrowRight />} {rotuloProximo}
        </Button>
      )}
    </div>
  );
}

function Dado({ rotulo, valor }: { rotulo: string; valor?: React.ReactNode }) {
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wide text-muted-foreground">{rotulo}</div>
      <div className="text-sm">{valor || "—"}</div>
    </div>
  );
}

function PaginaPedido() {
  const { id } = Route.useParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const permissao = usePermissao("vendas");
  const podePagar = usePodePagar();
  const { data: p } = useSuspenseQuery(pedidoQuery(Number(id)));

  function atualizar(novo: Pedido) {
    queryClient.setQueryData(chaves.detalhe(novo.id), novo);
    void queryClient.invalidateQueries({ queryKey: chaves.todos });
    void queryClient.invalidateQueries({ queryKey: ["produtos"] });
    void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  }

  const excluir = useMutation({
    mutationFn: () => excluirPedido(p.id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: chaves.todos });
      void queryClient.invalidateQueries({ queryKey: ["produtos"] });
      toast.success("Pedido excluído.");
      void router.navigate({ to: "/pedidos" });
    },
    onError: (erro: Error) => toast.error(erro.message),
  });
  const apagarPagamento = useMutation({
    mutationFn: (pid: number) => excluirPagamento(p.id, pid),
    onSuccess: atualizar,
    onError: (erro: Error) => toast.error(erro.message),
  });
  const comprovante = useMutation({
    mutationFn: (arquivo: File | null) => enviarComprovante(p.id, arquivo),
    onSuccess: (novo) => { atualizar(novo); toast.success("Comprovante atualizado."); },
    onError: (erro: Error) => toast.error(erro.message),
  });

  const titulo = p.numero || `Rascunho #${p.id}`;
  const cliente = p.cliente.nome_social || p.cliente.nome;

  return (
    <div className="space-y-6">
      <CabecalhoPagina
        titulo={titulo}
        voltar={{ para: "/pedidos", rotulo: "Pedidos" }}
        descricao={
          <span className="flex flex-wrap items-center gap-1.5">
            <Badge variant="secondary" className={cn("font-normal", COR_STATUS[p.status])}>{p.status_rotulo}</Badge>
            <Badge variant="secondary" className={cn("font-normal", COR_PAGAMENTO[p.status_pagamento])}>{p.status_pagamento_rotulo}</Badge>
            {p.estoque_baixado && <Badge variant="outline" className="font-normal">estoque baixado</Badge>}
            <span className="text-xs text-muted-foreground">
              {fmtData(p.data_compra)} · <Link to="/clientes/$id" params={{ id: String(p.cliente.id) }} className="hover:underline">{cliente}</Link>
            </span>
          </span>
        }
        acoes={
          <>
            <Button asChild size="sm" variant="outline">
              <a href={p.url_recibo} target="_blank" rel="noreferrer"><FileText /> Recibo</a>
            </Button>
            {permissao.escrever && (
              <Button asChild size="sm" variant="outline">
                <Link to="/pedidos/$id/editar" params={{ id }}><Pencil /> Editar</Link>
              </Button>
            )}
            {permissao.excluir && (
              <ConfirmarExclusao
                titulo={`Excluir ${titulo}?`}
                descricao={p.estoque_baixado ? "O estoque dos itens será estornado. Os pagamentos registrados também somem." : "Os pagamentos registrados também somem."}
                aoConfirmar={() => excluir.mutateAsync()}
                pendente={excluir.isPending}
              />
            )}
          </>
        }
      />

      {permissao.escrever && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-card px-4 py-3">
          <div className="text-sm">
            <span className="text-muted-foreground">Status:</span> <span className="font-medium">{p.status_rotulo}</span>
          </div>
          <MudarStatus pedido={p} aoAtualizar={atualizar} />
        </div>
      )}

      {p.faltas.length > 0 && !p.estoque_baixado && (
        <div className="flex items-start gap-2 rounded-xl border border-warning/40 bg-warning/10 px-4 py-3 text-sm">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-warning" />
          <div>
            <div className="font-medium">Estoque insuficiente para confirmar</div>
            <ul className="text-xs text-muted-foreground">
              {p.faltas.map((f) => <li key={f.produto_id}>{f.produto}: precisa {numero(f.necessario)}, tem {numero(f.disponivel)}</li>)}
            </ul>
          </div>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Itens</CardTitle>
            <CardDescription>{numero(p.itens.length)} {p.itens.length === 1 ? "item" : "itens"}</CardDescription>
          </CardHeader>
          <CardContent>
            {p.itens.length === 0 ? (
              <Vazio titulo="Sem itens" descricao="Edite o pedido para adicionar produtos." className="py-8" />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Produto</TableHead>
                    <TableHead className="text-right">Qtd.</TableHead>
                    <TableHead className="hidden text-right sm:table-cell">Preço un.</TableHead>
                    <TableHead className="hidden text-right md:table-cell">Desc.</TableHead>
                    <TableHead className="text-right">Total</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {p.itens.map((i) => (
                    <TableRow key={i.id}>
                      <TableCell>
                        <Link to="/produtos/$id" params={{ id: String(i.produto.id) }} className="font-medium hover:underline">{i.produto.nome_completo}</Link>
                        {i.produto.sku && <span className="ml-1 text-xs text-muted-foreground">{i.produto.sku}</span>}
                      </TableCell>
                      <TableCell className="tabular text-right">{numero(i.quantidade)}</TableCell>
                      <TableCell className="tabular hidden text-right text-muted-foreground sm:table-cell">{moeda(i.preco_unitario)}</TableCell>
                      <TableCell className="tabular hidden text-right text-muted-foreground md:table-cell">{i.desconto_item > 0 ? `−${moeda(i.desconto_item)}` : "—"}</TableCell>
                      <TableCell className="tabular text-right font-medium">{moeda(i.total)}</TableCell>
                    </TableRow>
                  ))}
                  <TableRow>
                    <TableCell colSpan={4} className="text-right text-muted-foreground">Subtotal</TableCell>
                    <TableCell className="tabular text-right">{moeda(p.subtotal)}</TableCell>
                  </TableRow>
                  {p.desconto > 0 && (
                    <TableRow>
                      <TableCell colSpan={4} className="text-right text-muted-foreground">Desconto</TableCell>
                      <TableCell className="tabular text-right">−{moeda(p.desconto)}</TableCell>
                    </TableRow>
                  )}
                  {p.taxa > 0 && (
                    <TableRow>
                      <TableCell colSpan={4} className="text-right text-muted-foreground">Taxa</TableCell>
                      <TableCell className="tabular text-right">+{moeda(p.taxa)}</TableCell>
                    </TableRow>
                  )}
                  <TableRow className="font-display text-base font-semibold">
                    <TableCell colSpan={4} className="text-right">Total</TableCell>
                    <TableCell className="tabular text-right">{moeda(p.valor_total)}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <div>
                <CardTitle>Pagamento</CardTitle>
                <CardDescription>{p.forma_pagamento_rotulo || "forma não informada"}</CardDescription>
              </div>
              {podePagar && p.status !== "cancelado" && <NovoPagamento pedido={p} aoAtualizar={atualizar} />}
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="text-[11px] uppercase tracking-wide text-muted-foreground">Pago</div>
                  <div className="tabular font-display text-xl font-semibold text-success">{moeda(p.total_pago)}</div>
                </div>
                <div>
                  <div className="text-[11px] uppercase tracking-wide text-muted-foreground">Em aberto</div>
                  <div className={cn("tabular font-display text-xl font-semibold", p.saldo_devedor > 0 ? "text-warning" : "")}>{moeda(Math.max(0, p.saldo_devedor))}</div>
                </div>
              </div>
              {p.pagamentos.length > 0 && (
                <ul className="divide-y text-sm">
                  {p.pagamentos.map((pg) => (
                    <li key={pg.id} className="group flex items-center justify-between gap-2 py-1.5">
                      <div>
                        <span className="tabular font-medium">{moeda(pg.valor)}</span>
                        <span className="ml-2 text-xs text-muted-foreground">{pg.forma_rotulo} · {fmtData(pg.data)}{pg.registrado_por && ` · ${pg.registrado_por.nome}`}</span>
                        {pg.observacao && <div className="text-xs text-muted-foreground">{pg.observacao}</div>}
                      </div>
                      {podePagar && (
                        <button type="button" onClick={() => apagarPagamento.mutate(pg.id)} className="text-muted-foreground opacity-0 hover:text-destructive group-hover:opacity-100 pointer-coarse:opacity-100" aria-label="Remover pagamento">
                          <Trash2 className="size-3.5" />
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
              )}
              <div className="flex items-center gap-2 border-t pt-3 text-xs">
                <Paperclip className="size-3.5 text-muted-foreground" />
                {p.comprovante ? (
                  <a href={p.comprovante} target="_blank" rel="noreferrer" className="hover:underline">ver comprovante</a>
                ) : (
                  <span className="text-muted-foreground">sem comprovante</span>
                )}
                {permissao.escrever && (
                  <label className="ml-auto cursor-pointer text-muted-foreground hover:text-foreground">
                    {comprovante.isPending ? "enviando…" : p.comprovante ? "trocar" : "anexar"}
                    <input type="file" className="hidden" accept="image/*,.pdf" onChange={(e) => e.target.files?.[0] && comprovante.mutate(e.target.files[0])} />
                  </label>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Entrega</CardTitle></CardHeader>
            <CardContent className="grid grid-cols-2 gap-3">
              <Dado rotulo="Previsão" valor={p.data_entrega ? fmtData(p.data_entrega) : ""} />
              <Dado rotulo="Local" valor={p.local_retirada} />
              <Dado rotulo="Responsável" valor={p.responsavel?.nome} />
              <Dado rotulo="Criado por" valor={p.criado_por ? `${p.criado_por.nome} · ${dataHora(p.criado_em)}` : dataHora(p.criado_em)} />
              {p.observacoes && <div className="col-span-2"><Dado rotulo="Observações" valor={<span className="whitespace-pre-line">{p.observacoes}</span>} /></div>}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
