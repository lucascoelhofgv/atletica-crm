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
import { cn } from "@/lib/utils";

import { opcoesEventoQuery } from "../api";
import type { Evento, EventoEntrada } from "../types";

const inteiroOpcional = z.number({ error: "Informe um número" }).int().min(0).nullable();

const esquema = z.object({
  nome: z.string().trim().min(2, "Informe o nome"),
  tipo: z.string().min(1, "Escolha o tipo"),
  descricao: z.string(),
  data: z.string().min(1, "Informe a data"),
  horario: z.string().trim(),
  local: z.string().trim(),
  capacidade: inteiroOpcional,
  publico_realizado: inteiroOpcional,
  staff_cortesias: z.number({ error: "Informe um número" }).int().min(0),
  status: z.string().min(1),
  publico_alvo: z.string().trim(),
  link_inscricao: z.string().trim().url("Link inválido").or(z.literal("")),
  orcamento_previsto: z.number({ error: "Informe um valor" }).min(0),
  responsavel_id: z.number().nullable(),
  fornecedores_ids: z.array(z.number()),
  observacoes: z.string(),
});
export type ValoresEvento = z.infer<typeof esquema>;

function hojeIso() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function iniciais(e?: Evento): ValoresEvento {
  return {
    nome: e?.nome ?? "",
    tipo: e?.tipo ?? "festa",
    descricao: e?.descricao ?? "",
    data: e?.data ?? hojeIso(),
    horario: e?.horario ?? "",
    local: e?.local ?? "",
    capacidade: e?.capacidade ?? null,
    publico_realizado: e?.publico_realizado ?? null,
    staff_cortesias: e?.staff_cortesias ?? 0,
    status: e?.status ?? "planejamento",
    publico_alvo: e?.publico_alvo ?? "",
    link_inscricao: e?.link_inscricao ?? "",
    orcamento_previsto: e?.orcamento_previsto ?? 0,
    responsavel_id: e?.responsavel?.id ?? null,
    fornecedores_ids: e?.fornecedores.map((f) => f.id) ?? [],
    observacoes: e?.observacoes ?? "",
  };
}

const NENHUM = "0";
const nulo = { setValueAs: (v: unknown) => (v === "" || v === null || v === undefined ? null : Number(v)) };

export function EventoForm({
  inicial,
  aoSalvar,
  salvando,
  rotuloSalvar = "Salvar",
  aoCancelar,
}: {
  inicial?: Evento;
  aoSalvar: (dados: EventoEntrada, form: ReturnType<typeof useForm<ValoresEvento>>) => void;
  salvando: boolean;
  rotuloSalvar?: string;
  aoCancelar: () => void;
}) {
  const { data: opcoes } = useQuery(opcoesEventoQuery);
  const form = useForm<ValoresEvento>({ resolver: zodResolver(esquema), defaultValues: iniciais(inicial) });
  const erros = form.formState.errors;
  const r = form.register;

  return (
    <form className="space-y-4" noValidate onSubmit={form.handleSubmit((v) => aoSalvar(v, form))}>
      <Secao titulo="Evento">
        <Campo id="nome" rotulo="Nome" obrigatorio erro={erros.nome?.message} className="sm:col-span-2">
          <Input id="nome" autoFocus {...r("nome")} aria-invalid={!!erros.nome} />
        </Campo>
        <Campo id="tipo" rotulo="Tipo" obrigatorio erro={erros.tipo?.message}>
          <Controller control={form.control} name="tipo" render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger id="tipo" className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent>{opcoes?.tipos.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}</SelectContent>
            </Select>
          )} />
        </Campo>
        <Campo id="status" rotulo="Status" erro={erros.status?.message}>
          <Controller control={form.control} name="status" render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger id="status" className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent>{opcoes?.status.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}</SelectContent>
            </Select>
          )} />
        </Campo>
        <Campo id="data" rotulo="Data" obrigatorio erro={erros.data?.message}>
          <Input id="data" type="date" {...r("data")} aria-invalid={!!erros.data} />
        </Campo>
        <Campo id="horario" rotulo="Horário" erro={erros.horario?.message}>
          <Input id="horario" placeholder="ex.: 22h às 4h" {...r("horario")} />
        </Campo>
        <Campo id="local" rotulo="Local" erro={erros.local?.message} className="sm:col-span-2">
          <Input id="local" {...r("local")} />
        </Campo>
        <Campo id="descricao" rotulo="Descrição" erro={erros.descricao?.message} className="sm:col-span-2">
          <Textarea id="descricao" rows={2} {...r("descricao")} />
        </Campo>
      </Secao>

      <Secao titulo="Público e orçamento" descricao="Ingressos, custos e receitas extras entram na tela do evento, depois de salvar.">
        <Campo id="capacidade" rotulo="Capacidade" erro={erros.capacidade?.message}>
          <Input id="capacidade" type="number" min="0" {...r("capacidade", nulo)} />
        </Campo>
        <Campo id="staff_cortesias" rotulo="Staff / cortesias" erro={erros.staff_cortesias?.message} ajuda="Entram sem pagar; não contam como receita">
          <Input id="staff_cortesias" type="number" min="0" {...r("staff_cortesias", { valueAsNumber: true })} />
        </Campo>
        <Campo id="publico_realizado" rotulo="Público realizado" erro={erros.publico_realizado?.message} ajuda="Preencha depois do evento, se souber o número real">
          <Input id="publico_realizado" type="number" min="0" {...r("publico_realizado", nulo)} />
        </Campo>
        <Campo id="orcamento_previsto" rotulo="Orçamento previsto (R$)" erro={erros.orcamento_previsto?.message}>
          <Input id="orcamento_previsto" type="number" step="0.01" min="0" {...r("orcamento_previsto", { valueAsNumber: true })} />
        </Campo>
        <Campo id="publico_alvo" rotulo="Público-alvo" erro={erros.publico_alvo?.message}>
          <Input id="publico_alvo" {...r("publico_alvo")} />
        </Campo>
        <Campo id="link_inscricao" rotulo="Link de inscrição / ingressos" erro={erros.link_inscricao?.message}>
          <Input id="link_inscricao" type="url" placeholder="https://…" {...r("link_inscricao")} aria-invalid={!!erros.link_inscricao} />
        </Campo>
      </Secao>

      <Secao titulo="Equipe e fornecedores">
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
        <Campo rotulo="Fornecedores envolvidos" className="sm:col-span-2">
          <Controller control={form.control} name="fornecedores_ids" render={({ field }) => (
            <div className="flex flex-wrap gap-2">
              {opcoes?.fornecedores.length === 0 && <span className="text-xs text-muted-foreground">Nenhum fornecedor ativo.</span>}
              {opcoes?.fornecedores.map((f) => {
                const ativo = field.value.includes(f.id);
                return (
                  <button key={f.id} type="button" aria-pressed={ativo}
                    onClick={() => field.onChange(ativo ? field.value.filter((id) => id !== f.id) : [...field.value, f.id])}
                    className={cn("rounded-full border px-3 py-1 text-xs transition-colors", ativo ? "border-primary bg-primary/15 text-primary" : "hover:bg-accent")}>
                    {f.nome_exibicao}
                  </button>
                );
              })}
            </div>
          )} />
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
