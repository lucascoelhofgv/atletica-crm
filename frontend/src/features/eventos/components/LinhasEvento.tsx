import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { LoaderCircle, Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Vazio } from "@/components/estado";
import { Campo } from "@/components/formulario";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { moeda, numero } from "@/lib/formatos";
import { cn } from "@/lib/utils";

import { adicionarLinha, alterarLinha, chaves, opcoesEventoQuery, removerLinha, type TipoLinha } from "../api";
import type { Custo, Evento, Lote, Receita } from "../types";

function useLinhas(evento: Evento, tipo: TipoLinha) {
  const queryClient = useQueryClient();
  const ok = (e: Evento) => {
    queryClient.setQueryData(chaves.detalhe(e.id), e);
    void queryClient.invalidateQueries({ queryKey: chaves.todos });
    void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  };
  const erro = (e: Error) => toast.error(e.message);
  const adicionar = useMutation({ mutationFn: (d: Record<string, unknown>) => adicionarLinha(evento.id, tipo, d as never), onSuccess: ok, onError: erro });
  const alterar = useMutation({ mutationFn: ({ id, d }: { id: number; d: Record<string, unknown> }) => alterarLinha(evento.id, tipo, id, d as never), onSuccess: ok, onError: erro });
  const remover = useMutation({ mutationFn: (id: number) => removerLinha(evento.id, tipo, id), onSuccess: ok, onError: erro });
  return { adicionar, alterar, remover };
}

const NENHUM = "0";
const num = (v: string) => (v === "" ? 0 : Number(v));

/* ------------------------------------------------------------------ Lotes */
export function Lotes({ evento, podeEditar }: { evento: Evento; podeEditar: boolean }) {
  const { adicionar, alterar, remover } = useLinhas(evento, "lotes");
  const [editando, setEditando] = useState<Partial<Lote> | null>(null);
  const [v, setV] = useState({ nome: "", quantidade_prevista: "0", quantidade_vendida: "0", valor_unitario: "0", ordem: "0" });
  function abrir(l?: Lote) {
    setEditando(l ?? {});
    setV({ nome: l?.nome ?? "", quantidade_prevista: String(l?.quantidade_prevista ?? 0), quantidade_vendida: String(l?.quantidade_vendida ?? 0), valor_unitario: String(l?.valor_unitario ?? 0), ordem: String(l?.ordem ?? evento.lotes.length) });
  }
  function salvar() {
    const d = { nome: v.nome.trim(), quantidade_prevista: num(v.quantidade_prevista), quantidade_vendida: num(v.quantidade_vendida), valor_unitario: num(v.valor_unitario), ordem: num(v.ordem) };
    if (!d.nome) return toast.error("Informe o nome do lote.");
    const m = editando?.id ? alterar.mutateAsync({ id: editando.id, d }) : adicionar.mutateAsync(d);
    void m.then(() => setEditando(null));
  }
  const pendente = adicionar.isPending || alterar.isPending;
  const f = evento.financeiro;
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle>Ingressos</CardTitle>
          <CardDescription>{numero(f.ingressos_vendidos)} vendidos de {numero(f.ingressos_previstos)} previstos · {moeda(f.receita_ingressos)}</CardDescription>
        </div>
        {podeEditar && <Button size="sm" variant="outline" onClick={() => abrir()}><Plus /> Lote</Button>}
      </CardHeader>
      <CardContent>
        {evento.lotes.length === 0 ? <Vazio titulo="Nenhum lote" descricao="Cadastre lotes (promocional, 1º lote, porta…) para acompanhar as vendas." className="py-6" /> : (
          <Table>
            <TableHeader><TableRow><TableHead>Lote</TableHead><TableHead className="text-right">Prev.</TableHead><TableHead className="text-right">Vend.</TableHead><TableHead className="text-right">Valor</TableHead><TableHead className="text-right">Receita</TableHead>{podeEditar && <TableHead className="w-16" />}</TableRow></TableHeader>
            <TableBody>
              {evento.lotes.map((l) => (
                <TableRow key={l.id}>
                  <TableCell className="font-medium">{l.nome}</TableCell>
                  <TableCell className="tabular text-right text-muted-foreground">{numero(l.quantidade_prevista)}</TableCell>
                  <TableCell className="tabular text-right">{numero(l.quantidade_vendida)}</TableCell>
                  <TableCell className="tabular text-right">{moeda(l.valor_unitario)}</TableCell>
                  <TableCell className="tabular text-right font-medium">{moeda(l.total_vendido)}</TableCell>
                  {podeEditar && <TableCell><Acoes aoEditar={() => abrir(l)} aoRemover={() => remover.mutate(l.id)} /></TableCell>}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
      <Dialog open={editando !== null} onOpenChange={(o) => !o && setEditando(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>{editando?.id ? "Editar lote" : "Novo lote"}</DialogTitle></DialogHeader>
          <div className="grid grid-cols-2 gap-3">
            <Campo id="l-nome" rotulo="Nome" obrigatorio className="col-span-2"><Input id="l-nome" autoFocus value={v.nome} onChange={(e) => setV({ ...v, nome: e.target.value })} placeholder="ex.: 1º lote" /></Campo>
            <Campo id="l-prev" rotulo="Qtd. prevista"><Input id="l-prev" type="number" min="0" value={v.quantidade_prevista} onChange={(e) => setV({ ...v, quantidade_prevista: e.target.value })} /></Campo>
            <Campo id="l-vend" rotulo="Qtd. vendida"><Input id="l-vend" type="number" min="0" value={v.quantidade_vendida} onChange={(e) => setV({ ...v, quantidade_vendida: e.target.value })} /></Campo>
            <Campo id="l-valor" rotulo="Valor unitário (R$)"><Input id="l-valor" type="number" step="0.01" min="0" value={v.valor_unitario} onChange={(e) => setV({ ...v, valor_unitario: e.target.value })} /></Campo>
            <Campo id="l-ordem" rotulo="Ordem"><Input id="l-ordem" type="number" min="0" value={v.ordem} onChange={(e) => setV({ ...v, ordem: e.target.value })} /></Campo>
          </div>
          <div className="flex justify-end gap-2"><Button variant="ghost" onClick={() => setEditando(null)}>Cancelar</Button><Button onClick={salvar} disabled={pendente}>{pendente && <LoaderCircle className="animate-spin" />} Salvar</Button></div>
        </DialogContent>
      </Dialog>
    </Card>
  );
}

/* ------------------------------------------------------------------ Custos */
const COR_SITUACAO: Record<string, string> = { pendente: "bg-warning/20 text-warning", parcial: "bg-primary/15 text-primary", pago: "bg-success/15 text-success" };

export function Custos({ evento, podeEditar }: { evento: Evento; podeEditar: boolean }) {
  const { adicionar, alterar, remover } = useLinhas(evento, "custos");
  const { data: opcoes } = useQuery(opcoesEventoQuery);
  const [editando, setEditando] = useState<Partial<Custo> | null>(null);
  const [v, setV] = useState({ tipo: "fixo", item: "", quantidade: "1", valor_unitario: "0", valor_pago: "0", situacao: "pendente", fornecedor_id: NENHUM, observacao: "" });
  function abrir(c?: Custo) {
    setEditando(c ?? {});
    setV({ tipo: c?.tipo ?? "fixo", item: c?.item ?? "", quantidade: String(c?.quantidade ?? 1), valor_unitario: String(c?.valor_unitario ?? 0), valor_pago: String(c?.valor_pago ?? 0), situacao: c?.situacao ?? "pendente", fornecedor_id: c?.fornecedor ? String(c.fornecedor.id) : NENHUM, observacao: c?.observacao ?? "" });
  }
  function salvar() {
    const d = { tipo: v.tipo, item: v.item.trim(), quantidade: num(v.quantidade), valor_unitario: num(v.valor_unitario), valor_pago: num(v.valor_pago), situacao: v.situacao, fornecedor_id: v.fornecedor_id === NENHUM ? null : Number(v.fornecedor_id), observacao: v.observacao };
    if (!d.item) return toast.error("Informe o item.");
    const m = editando?.id ? alterar.mutateAsync({ id: editando.id, d }) : adicionar.mutateAsync(d);
    void m.then(() => setEditando(null));
  }
  const pendente = adicionar.isPending || alterar.isPending;
  const f = evento.financeiro;
  const total = num(v.quantidade) * num(v.valor_unitario);
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle>Custos</CardTitle>
          <CardDescription>{moeda(f.custo_total)} no total · {moeda(f.custo_a_pagar)} a pagar</CardDescription>
        </div>
        {podeEditar && <Button size="sm" variant="outline" onClick={() => abrir()}><Plus /> Custo</Button>}
      </CardHeader>
      <CardContent>
        {evento.custos.length === 0 ? <Vazio titulo="Nenhum custo lançado" className="py-6" /> : (
          <Table>
            <TableHeader><TableRow><TableHead>Item</TableHead><TableHead className="hidden sm:table-cell">Tipo</TableHead><TableHead className="text-right">Total</TableHead><TableHead className="hidden text-right md:table-cell">Pago</TableHead><TableHead>Situação</TableHead>{podeEditar && <TableHead className="w-16" />}</TableRow></TableHeader>
            <TableBody>
              {evento.custos.map((c) => (
                <TableRow key={c.id}>
                  <TableCell>
                    <div className="font-medium">{c.item}</div>
                    <div className="text-xs text-muted-foreground">{numero(c.quantidade)} × {moeda(c.valor_unitario)}{c.fornecedor && ` · ${c.fornecedor.nome_exibicao}`}</div>
                  </TableCell>
                  <TableCell className="hidden text-muted-foreground sm:table-cell">{c.tipo_rotulo}</TableCell>
                  <TableCell className="tabular text-right font-medium">{moeda(c.valor_total)}</TableCell>
                  <TableCell className="tabular hidden text-right text-muted-foreground md:table-cell">{moeda(c.valor_pago)}</TableCell>
                  <TableCell><Badge variant="secondary" className={cn("font-normal", COR_SITUACAO[c.situacao])}>{c.situacao_rotulo}</Badge></TableCell>
                  {podeEditar && <TableCell><Acoes aoEditar={() => abrir(c)} aoRemover={() => remover.mutate(c.id)} /></TableCell>}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
      <Dialog open={editando !== null} onOpenChange={(o) => !o && setEditando(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>{editando?.id ? "Editar custo" : "Novo custo"}</DialogTitle></DialogHeader>
          <div className="grid grid-cols-2 gap-3">
            <Campo id="c-item" rotulo="Item" obrigatorio className="col-span-2"><Input id="c-item" autoFocus value={v.item} onChange={(e) => setV({ ...v, item: e.target.value })} placeholder="ex.: Som e iluminação" /></Campo>
            <Campo id="c-tipo" rotulo="Tipo">
              <Select value={v.tipo} onValueChange={(x) => setV({ ...v, tipo: x })}><SelectTrigger id="c-tipo" className="w-full"><SelectValue /></SelectTrigger><SelectContent>{opcoes?.tipos_custo.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}</SelectContent></Select>
            </Campo>
            <Campo id="c-sit" rotulo="Situação">
              <Select value={v.situacao} onValueChange={(x) => setV({ ...v, situacao: x })}><SelectTrigger id="c-sit" className="w-full"><SelectValue /></SelectTrigger><SelectContent>{opcoes?.situacoes_custo.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}</SelectContent></Select>
            </Campo>
            <Campo id="c-qtd" rotulo="Quantidade"><Input id="c-qtd" type="number" step="0.01" min="0" value={v.quantidade} onChange={(e) => setV({ ...v, quantidade: e.target.value })} /></Campo>
            <Campo id="c-vu" rotulo="Valor unitário (R$)" ajuda={`Total: ${moeda(total)}`}><Input id="c-vu" type="number" step="0.01" min="0" value={v.valor_unitario} onChange={(e) => setV({ ...v, valor_unitario: e.target.value })} /></Campo>
            <Campo id="c-pago" rotulo="Já pago (R$)"><Input id="c-pago" type="number" step="0.01" min="0" value={v.valor_pago} onChange={(e) => setV({ ...v, valor_pago: e.target.value })} /></Campo>
            <Campo id="c-forn" rotulo="Fornecedor">
              <Select value={v.fornecedor_id} onValueChange={(x) => setV({ ...v, fornecedor_id: x })}><SelectTrigger id="c-forn" className="w-full"><SelectValue /></SelectTrigger><SelectContent><SelectItem value={NENHUM}>Sem fornecedor</SelectItem>{opcoes?.fornecedores.map((f) => <SelectItem key={f.id} value={String(f.id)}>{f.nome_exibicao}</SelectItem>)}</SelectContent></Select>
            </Campo>
            <Campo id="c-obs" rotulo="Observação" className="col-span-2"><Input id="c-obs" value={v.observacao} onChange={(e) => setV({ ...v, observacao: e.target.value })} /></Campo>
          </div>
          <div className="flex justify-end gap-2"><Button variant="ghost" onClick={() => setEditando(null)}>Cancelar</Button><Button onClick={salvar} disabled={pendente}>{pendente && <LoaderCircle className="animate-spin" />} Salvar</Button></div>
        </DialogContent>
      </Dialog>
    </Card>
  );
}

/* ---------------------------------------------------------------- Receitas */
export function Receitas({ evento, podeEditar }: { evento: Evento; podeEditar: boolean }) {
  const { adicionar, alterar, remover } = useLinhas(evento, "receitas");
  const { data: opcoes } = useQuery(opcoesEventoQuery);
  const [editando, setEditando] = useState<Partial<Receita> | null>(null);
  const [v, setV] = useState({ origem: "outro", descricao: "", valor: "0", recebido: false });
  function abrir(r?: Receita) {
    setEditando(r ?? {});
    setV({ origem: r?.origem ?? "outro", descricao: r?.descricao ?? "", valor: String(r?.valor ?? 0), recebido: r?.recebido ?? false });
  }
  function salvar() {
    const d = { origem: v.origem, descricao: v.descricao.trim(), valor: num(v.valor), recebido: v.recebido };
    if (!d.descricao) return toast.error("Informe a descrição.");
    const m = editando?.id ? alterar.mutateAsync({ id: editando.id, d }) : adicionar.mutateAsync(d);
    void m.then(() => setEditando(null));
  }
  const pendente = adicionar.isPending || alterar.isPending;
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle>Receitas extras</CardTitle>
          <CardDescription>Bar, patrocínio, parcerias · {moeda(evento.financeiro.receita_extra)}</CardDescription>
        </div>
        {podeEditar && <Button size="sm" variant="outline" onClick={() => abrir()}><Plus /> Receita</Button>}
      </CardHeader>
      <CardContent>
        {evento.receitas.length === 0 ? <Vazio titulo="Nenhuma receita extra" className="py-6" /> : (
          <Table>
            <TableHeader><TableRow><TableHead>Descrição</TableHead><TableHead className="hidden sm:table-cell">Origem</TableHead><TableHead className="text-right">Valor</TableHead><TableHead>Recebido</TableHead>{podeEditar && <TableHead className="w-16" />}</TableRow></TableHeader>
            <TableBody>
              {evento.receitas.map((r) => (
                <TableRow key={r.id}>
                  <TableCell className="font-medium">{r.descricao}</TableCell>
                  <TableCell className="hidden text-muted-foreground sm:table-cell">{r.origem_rotulo}</TableCell>
                  <TableCell className="tabular text-right font-medium">{moeda(r.valor)}</TableCell>
                  <TableCell><Badge variant="secondary" className={cn("font-normal", r.recebido ? "bg-success/15 text-success" : "bg-warning/20 text-warning")}>{r.recebido ? "Recebido" : "A receber"}</Badge></TableCell>
                  {podeEditar && <TableCell><Acoes aoEditar={() => abrir(r)} aoRemover={() => remover.mutate(r.id)} /></TableCell>}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
      <Dialog open={editando !== null} onOpenChange={(o) => !o && setEditando(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>{editando?.id ? "Editar receita" : "Nova receita"}</DialogTitle></DialogHeader>
          <div className="grid grid-cols-2 gap-3">
            <Campo id="r-desc" rotulo="Descrição" obrigatorio className="col-span-2"><Input id="r-desc" autoFocus value={v.descricao} onChange={(e) => setV({ ...v, descricao: e.target.value })} placeholder="ex.: Patrocínio Academia X" /></Campo>
            <Campo id="r-origem" rotulo="Origem">
              <Select value={v.origem} onValueChange={(x) => setV({ ...v, origem: x })}><SelectTrigger id="r-origem" className="w-full"><SelectValue /></SelectTrigger><SelectContent>{opcoes?.origens_receita.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}</SelectContent></Select>
            </Campo>
            <Campo id="r-valor" rotulo="Valor (R$)"><Input id="r-valor" type="number" step="0.01" min="0" value={v.valor} onChange={(e) => setV({ ...v, valor: e.target.value })} /></Campo>
            <label className="col-span-2 flex cursor-pointer items-center gap-2 text-sm"><Checkbox checked={v.recebido} onCheckedChange={(x) => setV({ ...v, recebido: x === true })} /> Já recebido</label>
          </div>
          <div className="flex justify-end gap-2"><Button variant="ghost" onClick={() => setEditando(null)}>Cancelar</Button><Button onClick={salvar} disabled={pendente}>{pendente && <LoaderCircle className="animate-spin" />} Salvar</Button></div>
        </DialogContent>
      </Dialog>
    </Card>
  );
}

function Acoes({ aoEditar, aoRemover }: { aoEditar: () => void; aoRemover: () => void }) {
  return (
    <div className="flex justify-end gap-1">
      <Button variant="ghost" size="icon-sm" onClick={aoEditar} aria-label="Editar"><Pencil /></Button>
      <Button variant="ghost" size="icon-sm" className="text-muted-foreground hover:text-destructive" onClick={aoRemover} aria-label="Remover"><Trash2 /></Button>
    </div>
  );
}
