import type { FieldValues, Path, UseFormReturn } from "react-hook-form";
import { toast } from "sonner";

import { Label } from "@/components/ui/label";
import { ApiErro } from "@/lib/api";
import { cn } from "@/lib/utils";

/** Rótulo + controle + ajuda + erro, no mesmo ritmo em todos os formulários. */
export function Campo({
  id,
  rotulo,
  erro,
  ajuda,
  obrigatorio,
  className,
  children,
}: {
  id?: string;
  rotulo: string;
  erro?: string;
  ajuda?: string;
  obrigatorio?: boolean;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div className={cn("space-y-1.5", className)}>
      <Label htmlFor={id} className="text-xs text-muted-foreground">
        {rotulo}
        {obrigatorio && <span className="text-destructive"> *</span>}
      </Label>
      {children}
      {erro ? (
        <p className="text-xs text-destructive">{erro}</p>
      ) : ajuda ? (
        <p className="text-xs text-muted-foreground/70">{ajuda}</p>
      ) : null}
    </div>
  );
}

/** Bloco de campos com título (Identificação, Contato, ...). */
export function Secao({
  titulo,
  descricao,
  children,
}: {
  titulo: string;
  descricao?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-4 rounded-xl border bg-card p-4 sm:p-5">
      <div>
        <h2 className="font-display text-base font-semibold">{titulo}</h2>
        {descricao && <p className="text-xs text-muted-foreground">{descricao}</p>}
      </div>
      <div className="grid gap-4 sm:grid-cols-2">{children}</div>
    </section>
  );
}

/**
 * Leva os erros de validação da API (`erro.campos`) para os campos do
 * formulário; o que não tem campo vira toast.
 */
export function aplicarErrosApi<T extends FieldValues>(form: UseFormReturn<T>, erro: unknown) {
  if (!(erro instanceof ApiErro)) {
    toast.error(erro instanceof Error ? erro.message : "Erro inesperado.");
    return;
  }
  const campos = Object.entries(erro.campos);
  let algumNoForm = false;
  for (const [campo, mensagens] of campos) {
    if (campo in form.getValues()) {
      form.setError(campo as Path<T>, { message: mensagens.join(" ") });
      algumNoForm = true;
    }
  }
  if (!algumNoForm || erro.status !== 400) {
    toast.error(erro.message);
  } else {
    toast.error("Corrija os campos destacados.");
  }
}
