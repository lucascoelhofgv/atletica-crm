import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, LoaderCircle, Plus, Trash2 } from "lucide-react";
import { Controller, useFieldArray, useForm } from "react-hook-form";
import { z } from "zod";

import { BuscaCombobox, type OpcaoBusca } from "@/components/BuscaCombobox";
import { Campo, Secao } from "@/components/formulario";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { ClienteLista } from "@/features/clientes/types";
import type { ProdutoLista } from "@/features/produtos/types";
import { api, type Paginado } from "@/lib/api";
import { moeda, numero } from "@/lib/formatos";
import { cn } from "@/lib/utils";

import { opcoesPedidoQuery } from "../api";
import { STATUS_BAIXA } from "../status";
import type { Pedido, PedidoEntrada, StatusPedido } from "../types";

const itemSchema = z.object({
  id: z.number().optional(),
  produto: z.number({ error: "Escolha o produto" }).min(1, "Escolha o produto"),
  produto_rotulo: z.string(),
  estoque: z.number(),
  quantidade: z.number({ error: "Informe a quantidade" }).int().min(1, "Mínimo 1"),
  preco_unitario: z.number({ error: "Informe o preço" }).min(0, "Não pode ser negativo"),
  desconto_item: z.number({ error: "Informe o desconto" }).min(0, "Não pode ser negativo"),
});

const esquema = z.object({
  cliente: z.number({ error: "Escolha o cliente" }).min(1, "Escolha o cliente"),
  cliente_rotulo: z.string(),
  status: z.string().min(1),
  forma_pagamento: z.string(),
  data_compra: z.string().min(1, "Informe a data"),
  data_entrega: z.string(),
  local_retirada: z.string().trim(),
  responsavel: z.number().nullable(),
  desconto: z.number({ error: "Informe o desconto" }).min(0),
  taxa: z.number({ error: "Informe a taxa" }).min(0),
  observacoes: z.string(),
  itens: z.array(itemSchema),
});
export type ValoresPedido = z.infer<typeof esquema>;

function hojeIso() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function iniciais(p?: Pedido): ValoresPedido {
  return {
    cliente: p?.cliente.id ?? 0,
    cliente_rotulo: p ? p.cliente.nome_social || p.cliente.nome : "",
    status: p?.status ?? "rascunho",
    forma_pagamento: p?.forma_pagamento ?? "pix",
    data_compra: p?.data_compra ?? hojeIso(),
    data_entrega: p?.data_entrega ?? "",
    local_retirada: p?.local_retirada ?? "",
    responsavel: p?.responsavel?.id ?? null,
    desconto: p?.desconto ?? 0,
    taxa: p?.taxa ?? 0,
    observacoes: p?.observacoes ?? "",
    itens:
      p?.itens.map((i) => ({
        id: i.id,
        produto: i.produto.id,
        produto_rotulo: i.produto.nome_completo,
        estoque: i.produto.quantidade_atual,
        quantidade: i.quantidade,
        preco_unitario: i.preco_unitario,
        desconto_item: i.desconto_item,
      })) ?? [],
  };
}

async function buscarClientes(termo: string): Promise<OpcaoBusca[]> {
  const r = await api<Paginado<ClienteLista>>("clientes/", { params: { q: termo, tamanho: 12 } });
  return r.resultados.map((c) => ({
    id: c.id,
    rotulo: c.nome_social || c.nome,
    detalhe: [c.email, c.whatsapp, c.curso].filter(Boolean).join(" · "),
  }));
}

async function buscarProdutos(termo: string): Promise<(OpcaoBusca & { preco: number; estoque: number })[]> {
  const r = await api<Paginado<ProdutoLista>>("produtos/", { params: { q: termo, status: "ativo", tamanho: 15 } });
  return r.resultados.map((p) => ({
    id: p.id,
    rotulo: p.nome_completo,
    detalhe: `${moeda(p.preco_venda)} · ${numero(p.quantidade_atual)} em estoque`,
    preco: p.preco_venda,
    estoque: p.quantidade_atual,
  }));
}

const NENHUM = "0";

export function PedidoForm({
  inicial,
  aoSalvar,
  salvando,
  rotuloSalvar = "Salvar",
  aoCancelar,
}: {
  inicial?: Pedido;
  aoSalvar: (dados: PedidoEntrada, form: ReturnType<typeof useForm<ValoresPedido>>) => void;
  salvando: boolean;
  rotuloSalvar?: string;
  aoCancelar: () => void;
}) {
  const { data: opcoes } = useQuery(opcoesPedidoQuery);
  const form = useForm<ValoresPedido>({ resolver: zodResolver(esquema), defaultValues: iniciais(inicial) });
  const { fields, append, remove } = useFieldArray({ control: form.control, name: "itens" });
  const erros = form.formState.errors;
  const r = form.register;

  const itens = form.watch("itens");
  const desconto = Number(form.watch("desconto")) || 0;
  const taxa = Number(form.watch("taxa")) || 0;
  const status = form.watch("status") as StatusPedido;
  const subtotal = itens.reduce((s, i) => s + (Number(i.preco_unitario) || 0) * (Number(i.quantidade) || 0) - (Number(i.desconto_item) || 0), 0);
  const total = Math.max(0, subtotal - desconto + taxa);
  const vaiBaixar = STATUS_BAIXA.has(status) && !inicial?.estoque_baixado;
  const faltas = itens.filter((i) => i.produto && (Number(i.quantidade) || 0) > i.estoque);

  function enviar(v: ValoresPedido) {
    aoSalvar(
      {
        cliente: v.cliente,
        status: v.status as StatusPedido,
        forma_pagamento: v.forma_pagamento,
        desconto: v.desconto,
        taxa: v.taxa,
        data_compra: v.data_compra,
        data_entrega: v.data_entrega || null,
        local_retirada: v.local_retirada,
        responsavel: v.responsavel,
        observacoes: v.observacoes,
        itens: v.itens.map((i) => ({
          id: i.id,
          produto: i.produto,
          quantidade: i.quantidade,
          preco_unitario: i.preco_unitario,
          desconto_item: i.desconto_item,
        })),
      },
      form,
    );
  }

  return (
    <form className="space-y-4" noValidate onSubmit={form.handleSubmit(enviar)}>
      <Secao titulo="Pedido">
        <Campo id="cliente" rotulo="Cliente" obrigatorio erro={erros.cliente?.message} className="sm:col-span-2">
          <Controller
            control={form.control}
            name="cliente"
            render={({ field }) => (
              <BuscaCombobox
                id="cliente"
                chave="clientes"
                valor={field.value || null}
                rotuloSelecionado={form.watch("cliente_rotulo")}
                buscar={buscarClientes}
                placeholder="Buscar cliente por nome, e-mail, WhatsApp…"
                invalido={!!erros.cliente}
                aoEscolher={(o) => {
                  field.onChange(o?.id ?? 0);
                  form.setValue("cliente_rotulo", o?.rotulo ?? "");
                }}
              />
            )}
          />
        </Campo>
        <Campo id="status" rotulo="Status" obrigatorio erro={erros.status?.message}
          ajuda={vaiBaixar ? "Este status baixa o estoque dos itens ao salvar." : undefined}>
          <Controller
            control={form.control}
            name="status"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger id="status" className="w-full"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {opcoes?.status.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
                </SelectContent>
              </Select>
            )}
          />
        </Campo>
        <Campo id="forma_pagamento" rotulo="Forma de pagamento" erro={erros.forma_pagamento?.message}>
          <Controller
            control={form.control}
            name="forma_pagamento"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger id="forma_pagamento" className="w-full"><SelectValue placeholder="Escolha" /></SelectTrigger>
                <SelectContent>
                  {opcoes?.formas_pagamento.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
                </SelectContent>
              </Select>
            )}
          />
        </Campo>
        <Campo id="data_compra" rotulo="Data da compra" obrigatorio erro={erros.data_compra?.message}>
          <Input id="data_compra" type="date" {...r("data_compra")} aria-invalid={!!erros.data_compra} />
        </Campo>
        <Campo id="data_entrega" rotulo="Entrega / retirada prevista" erro={erros.data_entrega?.message}>
          <Input id="data_entrega" type="date" {...r("data_entrega")} />
        </Campo>
        <Campo id="local_retirada" rotulo="Local de retirada" erro={erros.local_retirada?.message}>
          <Input id="local_retirada" placeholder="ex.: sala da Atlética" {...r("local_retirada")} />
        </Campo>
        <Campo id="responsavel" rotulo="Responsável" erro={erros.responsavel?.message}>
          <Controller
            control={form.control}
            name="responsavel"
            render={({ field }) => (
              <Select value={field.value === null ? NENHUM : String(field.value)} onValueChange={(v) => field.onChange(v === NENHUM ? null : Number(v))}>
                <SelectTrigger id="responsavel" className="w-full"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value={NENHUM}>Sem responsável</SelectItem>
                  {opcoes?.membros.map((m) => <SelectItem key={m.id} value={String(m.id)}>{m.nome}</SelectItem>)}
                </SelectContent>
              </Select>
            )}
          />
        </Campo>
      </Secao>

      <section className="space-y-3 rounded-xl border bg-card p-4 sm:p-5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-display text-base font-semibold">Itens</h2>
            <p className="text-xs text-muted-foreground">O preço vem do cadastro do produto, mas pode ser ajustado.</p>
          </div>
          <Button type="button" size="sm" variant="outline" onClick={() => append({ produto: 0, produto_rotulo: "", estoque: 0, quantidade: 1, preco_unitario: 0, desconto_item: 0 })}>
            <Plus /> Adicionar item
          </Button>
        </div>
        {typeof erros.itens?.message === "string" && <p className="text-xs text-destructive">{erros.itens.message}</p>}

        {fields.length === 0 ? (
          <p className="rounded-lg border border-dashed px-4 py-6 text-center text-sm text-muted-foreground">
            Nenhum item. Um rascunho pode ficar sem itens; para confirmar a venda, adicione pelo menos um.
          </p>
        ) : (
          <div className="space-y-2">
            <div className="hidden grid-cols-[1fr_5rem_7rem_7rem_6rem_2rem] gap-2 px-1 text-[11px] uppercase tracking-wide text-muted-foreground md:grid">
              <span>Produto</span><span>Qtd.</span><span>Preço un.</span><span>Desc. item</span><span className="text-right">Total</span><span />
            </div>
            {fields.map((campo, i) => {
              const item = itens[i];
              const totalItem = (Number(item?.preco_unitario) || 0) * (Number(item?.quantidade) || 0) - (Number(item?.desconto_item) || 0);
              const semEstoque = item?.produto && (Number(item.quantidade) || 0) > item.estoque;
              const e = erros.itens?.[i];
              return (
                <div key={campo.id} className={cn("grid grid-cols-2 items-start gap-2 rounded-lg border p-2 md:grid-cols-[1fr_5rem_7rem_7rem_6rem_2rem] md:border-0 md:p-1", semEstoque && "border-warning/50")}>
                  <div className="col-span-2 md:col-span-1">
                    <Controller
                      control={form.control}
                      name={`itens.${i}.produto`}
                      render={({ field }) => (
                        <BuscaCombobox
                          chave="produtos"
                          valor={field.value || null}
                          rotuloSelecionado={item?.produto_rotulo}
                          buscar={buscarProdutos}
                          placeholder="Buscar produto…"
                          invalido={!!e?.produto}
                          aoEscolher={(o) => {
                            const op = o as (OpcaoBusca & { preco: number; estoque: number }) | null;
                            field.onChange(op?.id ?? 0);
                            form.setValue(`itens.${i}.produto_rotulo`, op?.rotulo ?? "");
                            form.setValue(`itens.${i}.estoque`, op?.estoque ?? 0);
                            if (op) form.setValue(`itens.${i}.preco_unitario`, op.preco);
                          }}
                        />
                      )}
                    />
                    {e?.produto && <p className="mt-1 text-xs text-destructive">{e.produto.message}</p>}
                    {semEstoque && (
                      <p className="mt-1 flex items-center gap-1 text-xs text-warning">
                        <AlertTriangle className="size-3" /> só {numero(item.estoque)} em estoque
                      </p>
                    )}
                  </div>
                  <Input type="number" min="1" aria-label="Quantidade" {...r(`itens.${i}.quantidade`, { valueAsNumber: true })} aria-invalid={!!e?.quantidade} />
                  <Input type="number" step="0.01" min="0" aria-label="Preço unitário" {...r(`itens.${i}.preco_unitario`, { valueAsNumber: true })} aria-invalid={!!e?.preco_unitario} />
                  <Input type="number" step="0.01" min="0" aria-label="Desconto do item" {...r(`itens.${i}.desconto_item`, { valueAsNumber: true })} aria-invalid={!!e?.desconto_item} />
                  <div className="tabular self-center text-right text-sm font-medium">{moeda(totalItem)}</div>
                  <Button type="button" variant="ghost" size="icon-sm" className="self-center text-muted-foreground hover:text-destructive" onClick={() => remove(i)} aria-label="Remover item">
                    <Trash2 />
                  </Button>
                </div>
              );
            })}
          </div>
        )}

        <div className="grid gap-3 border-t pt-3 sm:grid-cols-[1fr_auto]">
          <div className="grid grid-cols-2 gap-3 sm:max-w-xs">
            <Campo id="desconto" rotulo="Desconto (R$)" erro={erros.desconto?.message}>
              <Input id="desconto" type="number" step="0.01" min="0" {...r("desconto", { valueAsNumber: true })} />
            </Campo>
            <Campo id="taxa" rotulo="Taxa (R$)" erro={erros.taxa?.message}>
              <Input id="taxa" type="number" step="0.01" min="0" {...r("taxa", { valueAsNumber: true })} />
            </Campo>
          </div>
          <div className="space-y-1 text-right text-sm">
            <div className="text-muted-foreground">Subtotal <span className="tabular ml-3 inline-block w-28">{moeda(subtotal)}</span></div>
            {(desconto > 0 || taxa > 0) && (
              <div className="text-muted-foreground">
                {desconto > 0 && <>Desconto <span className="tabular ml-3 inline-block w-28">−{moeda(desconto)}</span></>}
                {taxa > 0 && <div>Taxa <span className="tabular ml-3 inline-block w-28">+{moeda(taxa)}</span></div>}
              </div>
            )}
            <div className="font-display text-lg font-semibold">Total <span className="tabular ml-3 inline-block w-28">{moeda(total)}</span></div>
          </div>
        </div>
        {vaiBaixar && faltas.length > 0 && (
          <p className="flex items-center gap-2 rounded-lg border border-warning/40 bg-warning/10 px-3 py-2 text-xs">
            <AlertTriangle className="size-4 shrink-0 text-warning" />
            O status escolhido baixa o estoque, mas {faltas.length === 1 ? "um item" : `${faltas.length} itens`} não tem saldo suficiente. O servidor vai recusar.
          </p>
        )}
      </section>

      <Secao titulo="Observações">
        <Campo id="observacoes" rotulo="Observações" erro={erros.observacoes?.message} className="sm:col-span-2">
          <Textarea id="observacoes" rows={2} {...r("observacoes")} />
        </Campo>
      </Secao>

      <div className="flex items-center justify-end gap-2">
        <Button type="button" variant="ghost" onClick={aoCancelar} disabled={salvando}>Cancelar</Button>
        <Button type="submit" disabled={salvando}>
          {salvando && <LoaderCircle className="animate-spin" />}
          {rotuloSalvar}
        </Button>
      </div>
    </form>
  );
}
