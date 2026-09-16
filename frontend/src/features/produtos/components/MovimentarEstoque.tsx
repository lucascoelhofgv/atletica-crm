import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDownUp, LoaderCircle } from "lucide-react";
import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { aplicarErrosApi, Campo } from "@/components/formulario";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { numero } from "@/lib/formatos";

import { chaves, movimentarEstoque, opcoesProdutoQuery } from "../api";
import type { Produto } from "../types";

const ENTRADAS = new Set(["entrada", "ajuste_pos", "devolucao"]);

const esquema = z.object({
  tipo: z.string().min(1, "Escolha o tipo"),
  quantidade: z.number({ error: "Informe a quantidade" }).int().min(1, "Mínimo 1"),
  motivo: z.string().trim().max(160),
  observacao: z.string().trim().max(255),
});

export function MovimentarEstoque({ produto }: { produto: Produto }) {
  const [aberto, setAberto] = useState(false);
  const queryClient = useQueryClient();
  const { data: opcoes } = useQuery(opcoesProdutoQuery);
  const form = useForm<z.infer<typeof esquema>>({
    resolver: zodResolver(esquema),
    defaultValues: { tipo: "entrada", quantidade: 1, motivo: "", observacao: "" },
  });
  const mover = useMutation({
    mutationFn: (d: z.infer<typeof esquema>) => movimentarEstoque(produto.id, d),
    onSuccess: ({ produto: atualizado, movimentacao }) => {
      queryClient.setQueryData(chaves.detalhe(produto.id), atualizado);
      void queryClient.invalidateQueries({ queryKey: chaves.todos });
      void queryClient.invalidateQueries({ queryKey: ["movimentacoes"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success(`${movimentacao.tipo_rotulo}: saldo agora é ${numero(movimentacao.saldo_apos ?? 0)}.`);
      form.reset();
      setAberto(false);
    },
    onError: (erro) => aplicarErrosApi(form, erro),
  });
  const erros = form.formState.errors;
  const tipo = form.watch("tipo");
  const qtd = Number(form.watch("quantidade")) || 0;
  const previsto = produto.quantidade_atual + (ENTRADAS.has(tipo) ? qtd : -qtd);

  return (
    <Dialog open={aberto} onOpenChange={setAberto}>
      <DialogTrigger asChild>
        <Button size="sm"><ArrowDownUp /> Movimentar estoque</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Movimentar estoque</DialogTitle>
          <DialogDescription>
            {produto.nome_completo} · saldo atual {numero(produto.quantidade_atual)}. Toda movimentação fica no histórico.
          </DialogDescription>
        </DialogHeader>
        <form className="space-y-4" noValidate onSubmit={form.handleSubmit((d) => mover.mutate(d))}>
          <Campo id="tipo" rotulo="Tipo" obrigatorio erro={erros.tipo?.message}>
            <Controller
              control={form.control}
              name="tipo"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger id="tipo" className="w-full"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {opcoes?.tipos_movimentacao.map((o) => <SelectItem key={o.valor} value={o.valor}>{o.rotulo}</SelectItem>)}
                  </SelectContent>
                </Select>
              )}
            />
          </Campo>
          <Campo id="quantidade" rotulo="Quantidade" obrigatorio erro={erros.quantidade?.message}
            ajuda={qtd > 0 ? `Saldo depois: ${numero(previsto)}${previsto < 0 ? " (fica negativo)" : ""}` : undefined}>
            <Input id="quantidade" type="number" min="1" autoFocus {...form.register("quantidade", { valueAsNumber: true })} aria-invalid={!!erros.quantidade} />
          </Campo>
          <Campo id="motivo" rotulo="Motivo" erro={erros.motivo?.message}>
            <Input id="motivo" placeholder="ex.: compra do fornecedor, contagem, avaria" {...form.register("motivo")} />
          </Campo>
          <Campo id="observacao" rotulo="Observação" erro={erros.observacao?.message}>
            <Input id="observacao" {...form.register("observacao")} />
          </Campo>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" onClick={() => setAberto(false)}>Cancelar</Button>
            <Button type="submit" disabled={mover.isPending}>
              {mover.isPending && <LoaderCircle className="animate-spin" />} Registrar
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
