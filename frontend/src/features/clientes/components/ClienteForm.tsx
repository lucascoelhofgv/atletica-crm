import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery } from "@tanstack/react-query";
import { LoaderCircle } from "lucide-react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { Campo, Secao } from "@/components/formulario";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

import { opcoesClienteQuery } from "../api";
import type { Cliente, ClienteEntrada } from "../types";

const esquema = z.object({
  nome: z.string().trim().min(2, "Informe o nome completo"),
  nome_social: z.string().trim(),
  cpf: z.string().trim().max(14, "CPF inválido"),
  data_nascimento: z.string().nullable(),
  email: z.string().trim().email("E-mail inválido").or(z.literal("")),
  telefone: z.string().trim(),
  whatsapp: z.string().trim(),
  cidade: z.string().trim(),
  endereco: z.string().trim(),
  membro_fgv: z.boolean(),
  vinculo: z.string().min(1, "Escolha o vínculo"),
  curso: z.string().trim(),
  periodo: z.string().trim(),
  campus: z.string().trim(),
  turma: z.string().trim(),
  categoria_id: z.number().nullable(),
  tags_ids: z.array(z.number()),
  origem: z.string().trim(),
  relacionamento: z.string().min(1, "Escolha o status"),
  aceita_comunicacoes: z.boolean(),
  observacoes: z.string(),
});
export type ValoresCliente = z.infer<typeof esquema>;

export function valoresIniciais(c?: Cliente): ValoresCliente {
  return {
    nome: c?.nome ?? "",
    nome_social: c?.nome_social ?? "",
    cpf: c?.cpf ?? "",
    data_nascimento: c?.data_nascimento ?? null,
    email: c?.email ?? "",
    telefone: c?.telefone ?? "",
    whatsapp: c?.whatsapp ?? "",
    cidade: c?.cidade ?? "",
    endereco: c?.endereco ?? "",
    membro_fgv: c?.membro_fgv ?? true,
    vinculo: c?.vinculo ?? "aluno",
    curso: c?.curso ?? "",
    periodo: c?.periodo ?? "",
    campus: c?.campus ?? "",
    turma: c?.turma ?? "",
    categoria_id: c?.categoria?.id ?? null,
    tags_ids: c?.tags.map((t) => t.id) ?? [],
    origem: c?.origem ?? "",
    relacionamento: c?.relacionamento ?? "novo",
    aceita_comunicacoes: c?.aceita_comunicacoes ?? false,
    observacoes: c?.observacoes ?? "",
  };
}

const SEM_CATEGORIA = "0";

export function ClienteForm({
  inicial,
  aoSalvar,
  salvando,
  rotuloSalvar = "Salvar",
  aoCancelar,
}: {
  inicial?: Cliente;
  aoSalvar: (dados: ClienteEntrada, form: ReturnType<typeof useForm<ValoresCliente>>) => void;
  salvando: boolean;
  rotuloSalvar?: string;
  aoCancelar: () => void;
}) {
  const { data: opcoes } = useQuery(opcoesClienteQuery);
  const form = useForm<ValoresCliente>({
    resolver: zodResolver(esquema),
    defaultValues: valoresIniciais(inicial),
  });
  const erros = form.formState.errors;
  const r = form.register;

  return (
    <form
      className="space-y-4"
      noValidate
      onSubmit={form.handleSubmit((v) => aoSalvar({ ...v, data_nascimento: v.data_nascimento || null }, form))}
    >
      <Secao titulo="Identificação">
        <Campo id="nome" rotulo="Nome completo" obrigatorio erro={erros.nome?.message} className="sm:col-span-2">
          <Input id="nome" autoFocus {...r("nome")} aria-invalid={!!erros.nome} />
        </Campo>
        <Campo id="nome_social" rotulo="Nome social" erro={erros.nome_social?.message}>
          <Input id="nome_social" {...r("nome_social")} />
        </Campo>
        <Campo id="cpf" rotulo="CPF" erro={erros.cpf?.message}>
          <Input id="cpf" placeholder="000.000.000-00" {...r("cpf")} aria-invalid={!!erros.cpf} />
        </Campo>
        <Campo id="data_nascimento" rotulo="Data de nascimento" erro={erros.data_nascimento?.message}>
          <Input id="data_nascimento" type="date" {...r("data_nascimento")} />
        </Campo>
      </Secao>

      <Secao titulo="Contato">
        <Campo id="email" rotulo="E-mail" erro={erros.email?.message}>
          <Input id="email" type="email" autoComplete="off" {...r("email")} aria-invalid={!!erros.email} />
        </Campo>
        <Campo id="whatsapp" rotulo="WhatsApp" erro={erros.whatsapp?.message}>
          <Input id="whatsapp" placeholder="(21) 9…" {...r("whatsapp")} />
        </Campo>
        <Campo id="telefone" rotulo="Telefone" erro={erros.telefone?.message}>
          <Input id="telefone" {...r("telefone")} />
        </Campo>
        <Campo id="cidade" rotulo="Cidade" erro={erros.cidade?.message}>
          <Input id="cidade" {...r("cidade")} />
        </Campo>
        <Campo id="endereco" rotulo="Endereço" erro={erros.endereco?.message} className="sm:col-span-2">
          <Input id="endereco" {...r("endereco")} />
        </Campo>
      </Secao>

      <Secao titulo="Vínculo com a FGV">
        <Campo id="vinculo" rotulo="Tipo de vínculo" obrigatorio erro={erros.vinculo?.message}>
          <Controller
            control={form.control}
            name="vinculo"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger id="vinculo" className="w-full"><SelectValue placeholder="Escolha" /></SelectTrigger>
                <SelectContent>
                  {opcoes?.vinculos.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
                </SelectContent>
              </Select>
            )}
          />
        </Campo>
        <div className="flex items-end pb-2">
          <Controller
            control={form.control}
            name="membro_fgv"
            render={({ field }) => (
              <label className="flex cursor-pointer items-center gap-2 text-sm">
                <Checkbox checked={field.value} onCheckedChange={(v) => field.onChange(v === true)} />
                É da comunidade FGV
              </label>
            )}
          />
        </div>
        <Campo id="curso" rotulo="Curso" erro={erros.curso?.message}>
          <Input id="curso" {...r("curso")} />
        </Campo>
        <Campo id="periodo" rotulo="Período" erro={erros.periodo?.message}>
          <Input id="periodo" placeholder="ex.: 4º" {...r("periodo")} />
        </Campo>
        <Campo id="campus" rotulo="Campus" erro={erros.campus?.message}>
          <Input id="campus" {...r("campus")} />
        </Campo>
        <Campo id="turma" rotulo="Turma" erro={erros.turma?.message}>
          <Input id="turma" {...r("turma")} />
        </Campo>
      </Secao>

      <Secao titulo="Classificação">
        <Campo id="categoria" rotulo="Categoria" erro={erros.categoria_id?.message}>
          <Controller
            control={form.control}
            name="categoria_id"
            render={({ field }) => (
              <Select
                value={field.value === null ? SEM_CATEGORIA : String(field.value)}
                onValueChange={(v) => field.onChange(v === SEM_CATEGORIA ? null : Number(v))}
              >
                <SelectTrigger id="categoria" className="w-full"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value={SEM_CATEGORIA}>Sem categoria</SelectItem>
                  {opcoes?.categorias.map((c) => <SelectItem key={c.id} value={String(c.id)}>{c.nome}</SelectItem>)}
                </SelectContent>
              </Select>
            )}
          />
        </Campo>
        <Campo id="relacionamento" rotulo="Status do relacionamento" obrigatorio erro={erros.relacionamento?.message}>
          <Controller
            control={form.control}
            name="relacionamento"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger id="relacionamento" className="w-full"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {opcoes?.relacionamentos.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
                </SelectContent>
              </Select>
            )}
          />
        </Campo>
        <Campo rotulo="Tags" className="sm:col-span-2">
          <Controller
            control={form.control}
            name="tags_ids"
            render={({ field }) => (
              <div className="flex flex-wrap gap-2">
                {opcoes?.tags.length === 0 && <span className="text-xs text-muted-foreground">Nenhuma tag cadastrada.</span>}
                {opcoes?.tags.map((t) => {
                  const ativa = field.value.includes(t.id);
                  return (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => field.onChange(ativa ? field.value.filter((id) => id !== t.id) : [...field.value, t.id])}
                      className={cn(
                        "rounded-full border px-3 py-1 text-xs transition-colors",
                        ativa ? "border-transparent text-white" : "hover:bg-accent",
                      )}
                      style={ativa ? { background: t.cor } : undefined}
                      aria-pressed={ativa}
                    >
                      {t.nome}
                    </button>
                  );
                })}
              </div>
            )}
          />
        </Campo>
        <Campo id="origem" rotulo="Origem do contato" erro={erros.origem?.message} ajuda="Instagram, indicação, evento, balcão…">
          <Input id="origem" {...r("origem")} />
        </Campo>
        <div className="flex items-end pb-2">
          <Controller
            control={form.control}
            name="aceita_comunicacoes"
            render={({ field }) => (
              <label className="flex cursor-pointer items-center gap-2 text-sm">
                <Checkbox checked={field.value} onCheckedChange={(v) => field.onChange(v === true)} />
                Autoriza receber comunicações (LGPD)
              </label>
            )}
          />
        </div>
        <Campo id="observacoes" rotulo="Observações" erro={erros.observacoes?.message} className="sm:col-span-2">
          <Textarea id="observacoes" rows={3} {...r("observacoes")} />
        </Campo>
      </Secao>

      <div className="flex items-center justify-end gap-2">
        <Button type="button" variant="ghost" onClick={aoCancelar} disabled={salvando}>
          Cancelar
        </Button>
        <Button type="submit" disabled={salvando}>
          {salvando && <LoaderCircle className="animate-spin" />}
          {rotuloSalvar}
        </Button>
      </div>
    </form>
  );
}
