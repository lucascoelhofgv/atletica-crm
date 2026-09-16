import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery } from "@tanstack/react-query";
import { LoaderCircle } from "lucide-react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { BuscaCombobox, type OpcaoBusca } from "@/components/BuscaCombobox";
import { Campo, Secao } from "@/components/formulario";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { ClienteLista } from "@/features/clientes/types";
import type { FornecedorLista } from "@/features/fornecedores/types";
import type { PedidoLista } from "@/features/pedidos/types";
import { api, type Paginado } from "@/lib/api";
import { data as fmtData, moeda } from "@/lib/formatos";

import { opcoesTarefaQuery } from "../api";
import type { Prioridade, StatusTarefa, Tarefa, TarefaEntrada } from "../types";

const esquema = z.object({
  titulo: z.string().trim().min(2, "Informe o título"),
  descricao: z.string(),
  responsavel_id: z.number().nullable(),
  prazo: z.string(),
  prioridade: z.enum(["baixa", "normal", "alta", "urgente"]),
  status: z.enum(["a_fazer", "em_andamento", "aguardando", "concluida", "cancelada"]),
  cliente_id: z.number().nullable(),
  cliente_rotulo: z.string(),
  pedido_id: z.number().nullable(),
  pedido_rotulo: z.string(),
  fornecedor_id: z.number().nullable(),
  fornecedor_rotulo: z.string(),
});
export type ValoresTarefa = z.infer<typeof esquema>;

function iniciais(t?: Tarefa, responsavelPadrao?: number | null): ValoresTarefa {
  return {
    titulo: t?.titulo ?? "",
    descricao: t?.descricao ?? "",
    responsavel_id: t ? t.responsavel?.id ?? null : responsavelPadrao ?? null,
    prazo: t?.prazo ?? "",
    prioridade: t?.prioridade ?? "normal",
    status: t?.status ?? "a_fazer",
    cliente_id: t?.cliente?.id ?? null,
    cliente_rotulo: t?.cliente?.nome ?? "",
    pedido_id: t?.pedido?.id ?? null,
    pedido_rotulo: t?.pedido?.nome ?? "",
    fornecedor_id: t?.fornecedor?.id ?? null,
    fornecedor_rotulo: t?.fornecedor?.nome ?? "",
  };
}

const NENHUM = "0";

async function buscarClientes(termo: string): Promise<OpcaoBusca[]> {
  const r = await api<Paginado<ClienteLista>>("clientes/", { params: { q: termo, tamanho: 10 } });
  return r.resultados.map((c) => ({ id: c.id, rotulo: c.nome_social || c.nome, detalhe: c.email || c.whatsapp }));
}
async function buscarPedidos(termo: string): Promise<OpcaoBusca[]> {
  const r = await api<Paginado<PedidoLista>>("pedidos/", { params: { q: termo, tamanho: 10 } });
  return r.resultados.map((p) => ({ id: p.id, rotulo: `${p.numero || `rascunho #${p.id}`} · ${p.cliente.nome}`, detalhe: `${fmtData(p.data_compra)} · ${moeda(p.valor_total)} · ${p.status_rotulo}` }));
}
async function buscarFornecedores(termo: string): Promise<OpcaoBusca[]> {
  const r = await api<Paginado<FornecedorLista>>("fornecedores/", { params: { q: termo, tamanho: 10 } });
  return r.resultados.map((f) => ({ id: f.id, rotulo: f.nome_exibicao, detalhe: f.categoria_rotulo }));
}

export function TarefaForm({
  inicial,
  responsavelPadrao,
  aoSalvar,
  salvando,
  rotuloSalvar = "Salvar",
  aoCancelar,
}: {
  inicial?: Tarefa;
  responsavelPadrao?: number | null;
  aoSalvar: (dados: TarefaEntrada, form: ReturnType<typeof useForm<ValoresTarefa>>) => void;
  salvando: boolean;
  rotuloSalvar?: string;
  aoCancelar: () => void;
}) {
  const { data: opcoes } = useQuery(opcoesTarefaQuery);
  const form = useForm<ValoresTarefa>({ resolver: zodResolver(esquema), defaultValues: iniciais(inicial, responsavelPadrao) });
  const erros = form.formState.errors;
  const r = form.register;

  function enviar(v: ValoresTarefa) {
    aoSalvar({
      titulo: v.titulo, descricao: v.descricao, responsavel_id: v.responsavel_id,
      prazo: v.prazo || null, prioridade: v.prioridade as Prioridade, status: v.status as StatusTarefa,
      cliente_id: v.cliente_id, pedido_id: v.pedido_id, fornecedor_id: v.fornecedor_id,
    }, form);
  }

  return (
    <form className="space-y-4" noValidate onSubmit={form.handleSubmit(enviar)}>
      <Secao titulo="Tarefa">
        <Campo id="titulo" rotulo="Título" obrigatorio erro={erros.titulo?.message} className="sm:col-span-2">
          <Input id="titulo" autoFocus {...r("titulo")} aria-invalid={!!erros.titulo} />
        </Campo>
        <Campo id="descricao" rotulo="Descrição" erro={erros.descricao?.message} className="sm:col-span-2">
          <Textarea id="descricao" rows={3} {...r("descricao")} />
        </Campo>
        <Campo id="responsavel" rotulo="Responsável" erro={erros.responsavel_id?.message}>
          <Controller control={form.control} name="responsavel_id" render={({ field }) => (
            <Select value={field.value === null ? NENHUM : String(field.value)} onValueChange={(v) => field.onChange(v === NENHUM ? null : Number(v))}>
              <SelectTrigger id="responsavel" className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value={NENHUM}>Sem responsável</SelectItem>
                {opcoes?.membros.map((m) => <SelectItem key={m.id} value={String(m.id)}>{m.nome}</SelectItem>)}
              </SelectContent>
            </Select>
          )} />
        </Campo>
        <Campo id="prazo" rotulo="Prazo" erro={erros.prazo?.message}>
          <Input id="prazo" type="date" {...r("prazo")} />
        </Campo>
        <Campo id="prioridade" rotulo="Prioridade" erro={erros.prioridade?.message}>
          <Controller control={form.control} name="prioridade" render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger id="prioridade" className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent>
                {opcoes?.prioridades.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
              </SelectContent>
            </Select>
          )} />
        </Campo>
        <Campo id="status" rotulo="Status" erro={erros.status?.message}>
          <Controller control={form.control} name="status" render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger id="status" className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent>
                {opcoes?.status.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
              </SelectContent>
            </Select>
          )} />
        </Campo>
      </Secao>

      <Secao titulo="Vínculos" descricao="Opcional: liga a tarefa a um cliente, pedido ou fornecedor.">
        <Campo id="cliente" rotulo="Cliente">
          <Controller control={form.control} name="cliente_id" render={({ field }) => (
            <BuscaCombobox id="cliente" chave="clientes" valor={field.value} rotuloSelecionado={form.watch("cliente_rotulo")} buscar={buscarClientes} placeholder="Buscar cliente…"
              aoEscolher={(o) => { field.onChange(o?.id ?? null); form.setValue("cliente_rotulo", o?.rotulo ?? ""); }} />
          )} />
        </Campo>
        <Campo id="pedido" rotulo="Pedido">
          <Controller control={form.control} name="pedido_id" render={({ field }) => (
            <BuscaCombobox id="pedido" chave="pedidos" valor={field.value} rotuloSelecionado={form.watch("pedido_rotulo")} buscar={buscarPedidos} placeholder="Buscar pedido…"
              aoEscolher={(o) => { field.onChange(o?.id ?? null); form.setValue("pedido_rotulo", o?.rotulo ?? ""); }} />
          )} />
        </Campo>
        <Campo id="fornecedor" rotulo="Fornecedor">
          <Controller control={form.control} name="fornecedor_id" render={({ field }) => (
            <BuscaCombobox id="fornecedor" chave="fornecedores" valor={field.value} rotuloSelecionado={form.watch("fornecedor_rotulo")} buscar={buscarFornecedores} placeholder="Buscar fornecedor…"
              aoEscolher={(o) => { field.onChange(o?.id ?? null); form.setValue("fornecedor_rotulo", o?.rotulo ?? ""); }} />
          )} />
        </Campo>
        <div className="flex items-end text-xs text-muted-foreground">
          {(form.watch("cliente_id") || form.watch("pedido_id") || form.watch("fornecedor_id")) && (
            <Button type="button" variant="ghost" size="sm" onClick={() => {
              form.setValue("cliente_id", null); form.setValue("cliente_rotulo", "");
              form.setValue("pedido_id", null); form.setValue("pedido_rotulo", "");
              form.setValue("fornecedor_id", null); form.setValue("fornecedor_rotulo", "");
            }}>Limpar vínculos</Button>
          )}
        </div>
      </Secao>

      <div className="flex items-center justify-end gap-2">
        <Button type="button" variant="ghost" onClick={aoCancelar} disabled={salvando}>Cancelar</Button>
        <Button type="submit" disabled={salvando}>{salvando && <LoaderCircle className="animate-spin" />}{rotuloSalvar}</Button>
      </div>
    </form>
  );
}
