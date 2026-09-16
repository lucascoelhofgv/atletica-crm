import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery } from "@tanstack/react-query";
import { LoaderCircle } from "lucide-react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { Campo, Secao } from "@/components/formulario";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

import { opcoesFornecedorQuery } from "../api";
import type { Fornecedor, FornecedorEntrada } from "../types";

const esquema = z.object({
  nome: z.string().trim().min(2, "Informe a razão social ou nome"),
  nome_fantasia: z.string().trim(),
  documento: z.string().trim().max(20, "Documento inválido"),
  contato_nome: z.string().trim(),
  email: z.string().trim().email("E-mail inválido").or(z.literal("")),
  telefone: z.string().trim(),
  whatsapp: z.string().trim(),
  endereco: z.string().trim(),
  categoria: z.string().min(1, "Escolha a categoria"),
  produtos_servicos: z.string(),
  condicoes_comerciais: z.string(),
  prazo_medio_entrega: z.string().trim(),
  status: z.enum(["ativo", "inativo"]),
  observacoes: z.string(),
});
export type ValoresFornecedor = z.infer<typeof esquema>;

function iniciais(f?: Fornecedor): ValoresFornecedor {
  return {
    nome: f?.nome ?? "",
    nome_fantasia: f?.nome_fantasia ?? "",
    documento: f?.documento ?? "",
    contato_nome: f?.contato_nome ?? "",
    email: f?.email ?? "",
    telefone: f?.telefone ?? "",
    whatsapp: f?.whatsapp ?? "",
    endereco: f?.endereco ?? "",
    categoria: f?.categoria ?? "outros",
    produtos_servicos: f?.produtos_servicos ?? "",
    condicoes_comerciais: f?.condicoes_comerciais ?? "",
    prazo_medio_entrega: f?.prazo_medio_entrega ?? "",
    status: f?.status ?? "ativo",
    observacoes: f?.observacoes ?? "",
  };
}

export function FornecedorForm({
  inicial,
  aoSalvar,
  salvando,
  rotuloSalvar = "Salvar",
  aoCancelar,
}: {
  inicial?: Fornecedor;
  aoSalvar: (dados: FornecedorEntrada, form: ReturnType<typeof useForm<ValoresFornecedor>>) => void;
  salvando: boolean;
  rotuloSalvar?: string;
  aoCancelar: () => void;
}) {
  const { data: opcoes } = useQuery(opcoesFornecedorQuery);
  const form = useForm<ValoresFornecedor>({ resolver: zodResolver(esquema), defaultValues: iniciais(inicial) });
  const erros = form.formState.errors;
  const r = form.register;

  return (
    <form className="space-y-4" noValidate onSubmit={form.handleSubmit((v) => aoSalvar(v, form))}>
      <Secao titulo="Fornecedor">
        <Campo id="nome" rotulo="Razão social ou nome" obrigatorio erro={erros.nome?.message} className="sm:col-span-2">
          <Input id="nome" autoFocus {...r("nome")} aria-invalid={!!erros.nome} />
        </Campo>
        <Campo id="nome_fantasia" rotulo="Nome fantasia" erro={erros.nome_fantasia?.message}>
          <Input id="nome_fantasia" {...r("nome_fantasia")} />
        </Campo>
        <Campo id="documento" rotulo="CNPJ / CPF" erro={erros.documento?.message}>
          <Input id="documento" {...r("documento")} />
        </Campo>
        <Campo id="categoria" rotulo="Categoria" obrigatorio erro={erros.categoria?.message}>
          <Controller
            control={form.control}
            name="categoria"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger id="categoria" className="w-full"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {opcoes?.categorias.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
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
      </Secao>

      <Secao titulo="Contato">
        <Campo id="contato_nome" rotulo="Pessoa de contato" erro={erros.contato_nome?.message}>
          <Input id="contato_nome" {...r("contato_nome")} />
        </Campo>
        <Campo id="email" rotulo="E-mail" erro={erros.email?.message}>
          <Input id="email" type="email" {...r("email")} aria-invalid={!!erros.email} />
        </Campo>
        <Campo id="whatsapp" rotulo="WhatsApp" erro={erros.whatsapp?.message}>
          <Input id="whatsapp" {...r("whatsapp")} />
        </Campo>
        <Campo id="telefone" rotulo="Telefone" erro={erros.telefone?.message}>
          <Input id="telefone" {...r("telefone")} />
        </Campo>
        <Campo id="endereco" rotulo="Endereço" erro={erros.endereco?.message} className="sm:col-span-2">
          <Input id="endereco" {...r("endereco")} />
        </Campo>
      </Secao>

      <Secao titulo="Comercial">
        <Campo id="produtos_servicos" rotulo="Produtos ou serviços fornecidos" erro={erros.produtos_servicos?.message} className="sm:col-span-2">
          <Textarea id="produtos_servicos" rows={2} {...r("produtos_servicos")} />
        </Campo>
        <Campo id="condicoes_comerciais" rotulo="Condições comerciais" erro={erros.condicoes_comerciais?.message} className="sm:col-span-2" ajuda="Prazo de pagamento, mínimo por pedido, frete…">
          <Textarea id="condicoes_comerciais" rows={2} {...r("condicoes_comerciais")} />
        </Campo>
        <Campo id="prazo_medio_entrega" rotulo="Prazo médio de entrega" erro={erros.prazo_medio_entrega?.message}>
          <Input id="prazo_medio_entrega" placeholder="ex.: 15 dias úteis" {...r("prazo_medio_entrega")} />
        </Campo>
        <Campo id="observacoes" rotulo="Observações" erro={erros.observacoes?.message} className="sm:col-span-2">
          <Textarea id="observacoes" rows={2} {...r("observacoes")} />
        </Campo>
      </Secao>

      <div className="flex items-center justify-end gap-2">
        <Button type="button" variant="ghost" onClick={aoCancelar} disabled={salvando}>Cancelar</Button>
        <Button type="submit" disabled={salvando}>{salvando && <LoaderCircle className="animate-spin" />}{rotuloSalvar}</Button>
      </div>
    </form>
  );
}
