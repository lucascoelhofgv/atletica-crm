import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery } from "@tanstack/react-query";
import { ImageIcon, LoaderCircle, X } from "lucide-react";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { Campo, Secao } from "@/components/formulario";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { moeda, percentual } from "@/lib/formatos";

import { opcoesProdutoQuery } from "../api";
import type { Produto, ProdutoEntrada } from "../types";

const numero = (msg: string) => z.number({ error: msg }).min(0, "Não pode ser negativo");

const esquema = z
  .object({
    nome: z.string().trim().min(2, "Informe o nome"),
    codigo_interno: z.string().trim(),
    sku: z.string().trim(),
    categoria_id: z.number().nullable(),
    descricao: z.string(),
    tamanho: z.string().trim(),
    cor: z.string().trim(),
    marca: z.string().trim(),
    fornecedor_id: z.number().nullable(),
    custo_unitario: numero("Informe o custo"),
    preco_venda: numero("Informe o preço"),
    estoque_minimo: z.number({ error: "Informe um número" }).int().min(0),
    estoque_maximo: z.number({ error: "Informe um número" }).int().min(0).nullable(),
    localizacao: z.string().trim(),
    status: z.enum(["ativo", "inativo"]),
    observacoes: z.string(),
  })
  .refine((v) => v.estoque_maximo === null || v.estoque_maximo >= v.estoque_minimo, {
    path: ["estoque_maximo"],
    message: "Deve ser maior que o mínimo",
  });
export type ValoresProduto = z.infer<typeof esquema>;

function iniciais(p?: Produto): ValoresProduto {
  return {
    nome: p?.nome ?? "",
    codigo_interno: p?.codigo_interno ?? "",
    sku: p?.sku ?? "",
    categoria_id: p?.categoria?.id ?? null,
    descricao: p?.descricao ?? "",
    tamanho: p?.tamanho ?? "",
    cor: p?.cor ?? "",
    marca: p?.marca ?? "",
    fornecedor_id: p?.fornecedor?.id ?? null,
    custo_unitario: p?.custo_unitario ?? 0,
    preco_venda: p?.preco_venda ?? 0,
    estoque_minimo: p?.estoque_minimo ?? 0,
    estoque_maximo: p?.estoque_maximo ?? null,
    localizacao: p?.localizacao ?? "",
    status: p?.status ?? "ativo",
    observacoes: p?.observacoes ?? "",
  };
}

const NENHUM = "0";

export function ProdutoForm({
  inicial,
  aoSalvar,
  salvando,
  rotuloSalvar = "Salvar",
  aoCancelar,
}: {
  inicial?: Produto;
  aoSalvar: (dados: ProdutoEntrada, foto: File | null | undefined, form: ReturnType<typeof useForm<ValoresProduto>>) => void;
  salvando: boolean;
  rotuloSalvar?: string;
  aoCancelar: () => void;
}) {
  const { data: opcoes } = useQuery(opcoesProdutoQuery);
  const form = useForm<ValoresProduto>({ resolver: zodResolver(esquema), defaultValues: iniciais(inicial) });
  const erros = form.formState.errors;
  const r = form.register;
  // undefined = não mexeu na foto; null = remover; File = nova
  const [foto, setFoto] = useState<File | null | undefined>(undefined);
  const [previa, setPrevia] = useState<string | null>(inicial?.foto ?? null);
  const custo = Number(form.watch("custo_unitario")) || 0;
  const preco = Number(form.watch("preco_venda")) || 0;
  const margem = preco > 0 ? (preco - custo) / preco : null;

  function escolherFoto(arquivo: File | null) {
    setFoto(arquivo);
    setPrevia(arquivo ? URL.createObjectURL(arquivo) : null);
  }

  return (
    <form
      className="space-y-4"
      noValidate
      onSubmit={form.handleSubmit((v) => aoSalvar({ ...v, estoque_maximo: v.estoque_maximo ?? null }, foto, form))}
    >
      <Secao titulo="Produto">
        <Campo id="nome" rotulo="Nome" obrigatorio erro={erros.nome?.message} className="sm:col-span-2">
          <Input id="nome" autoFocus {...r("nome")} aria-invalid={!!erros.nome} />
        </Campo>
        <Campo id="tamanho" rotulo="Tamanho" erro={erros.tamanho?.message} ajuda="P, M, G, único…">
          <Input id="tamanho" {...r("tamanho")} />
        </Campo>
        <Campo id="cor" rotulo="Cor" erro={erros.cor?.message}>
          <Input id="cor" {...r("cor")} />
        </Campo>
        <Campo id="categoria" rotulo="Categoria" erro={erros.categoria_id?.message}>
          <Controller
            control={form.control}
            name="categoria_id"
            render={({ field }) => (
              <Select value={field.value === null ? NENHUM : String(field.value)} onValueChange={(v) => field.onChange(v === NENHUM ? null : Number(v))}>
                <SelectTrigger id="categoria" className="w-full"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value={NENHUM}>Sem categoria</SelectItem>
                  {opcoes?.categorias.map((c) => <SelectItem key={c.id} value={String(c.id)}>{c.nome}</SelectItem>)}
                </SelectContent>
              </Select>
            )}
          />
        </Campo>
        <Campo id="status" rotulo="Status" erro={erros.status?.message}>
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
        <Campo id="descricao" rotulo="Descrição" erro={erros.descricao?.message} className="sm:col-span-2">
          <Textarea id="descricao" rows={2} {...r("descricao")} />
        </Campo>
        <Campo rotulo="Foto" className="sm:col-span-2">
          <div className="flex items-center gap-3">
            <div className="flex size-16 shrink-0 items-center justify-center overflow-hidden rounded-lg border bg-muted">
              {previa ? <img src={previa} alt="" className="size-full object-cover" /> : <ImageIcon className="size-6 text-muted-foreground" />}
            </div>
            <Input type="file" accept="image/*" className="max-w-xs" onChange={(e) => escolherFoto(e.target.files?.[0] ?? null)} />
            {previa && (
              <Button type="button" variant="ghost" size="sm" onClick={() => escolherFoto(null)}><X /> Remover</Button>
            )}
          </div>
        </Campo>
      </Secao>

      <Secao titulo="Códigos e fornecedor">
        <Campo id="sku" rotulo="SKU" erro={erros.sku?.message}>
          <Input id="sku" {...r("sku")} />
        </Campo>
        <Campo id="codigo_interno" rotulo="Código interno" erro={erros.codigo_interno?.message}>
          <Input id="codigo_interno" {...r("codigo_interno")} />
        </Campo>
        <Campo id="marca" rotulo="Marca" erro={erros.marca?.message}>
          <Input id="marca" {...r("marca")} />
        </Campo>
        <Campo id="fornecedor" rotulo="Fornecedor" erro={erros.fornecedor_id?.message}>
          <Controller
            control={form.control}
            name="fornecedor_id"
            render={({ field }) => (
              <Select value={field.value === null ? NENHUM : String(field.value)} onValueChange={(v) => field.onChange(v === NENHUM ? null : Number(v))}>
                <SelectTrigger id="fornecedor" className="w-full"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value={NENHUM}>Sem fornecedor</SelectItem>
                  {opcoes?.fornecedores.map((f) => <SelectItem key={f.id} value={String(f.id)}>{f.nome_fantasia || f.nome}</SelectItem>)}
                </SelectContent>
              </Select>
            )}
          />
        </Campo>
      </Secao>

      <Secao titulo="Preço e estoque" descricao="O saldo em estoque muda só por movimentação, na tela do produto.">
        <Campo id="custo_unitario" rotulo="Custo unitário (R$)" obrigatorio erro={erros.custo_unitario?.message}>
          <Input id="custo_unitario" type="number" step="0.01" min="0" inputMode="decimal" {...r("custo_unitario", { valueAsNumber: true })} aria-invalid={!!erros.custo_unitario} />
        </Campo>
        <Campo id="preco_venda" rotulo="Preço de venda (R$)" obrigatorio erro={erros.preco_venda?.message}
          ajuda={margem !== null ? `Margem estimada: ${percentual(margem).replace("+", "")} (${moeda(preco - custo)} por unidade)` : undefined}>
          <Input id="preco_venda" type="number" step="0.01" min="0" inputMode="decimal" {...r("preco_venda", { valueAsNumber: true })} aria-invalid={!!erros.preco_venda} />
        </Campo>
        <Campo id="estoque_minimo" rotulo="Estoque mínimo" erro={erros.estoque_minimo?.message} ajuda="Abaixo disso o painel alerta">
          <Input id="estoque_minimo" type="number" min="0" {...r("estoque_minimo", { valueAsNumber: true })} />
        </Campo>
        <Campo id="estoque_maximo" rotulo="Estoque máximo" erro={erros.estoque_maximo?.message}>
          <Input id="estoque_maximo" type="number" min="0" {...r("estoque_maximo", { setValueAs: (v) => (v === "" || v === null || v === undefined ? null : Number(v)) })} />
        </Campo>
        <Campo id="localizacao" rotulo="Localização física" erro={erros.localizacao?.message} ajuda="ex.: armário da sala, caixa 2">
          <Input id="localizacao" {...r("localizacao")} />
        </Campo>
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
