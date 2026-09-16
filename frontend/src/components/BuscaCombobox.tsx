import { useQuery } from "@tanstack/react-query";
import { Check, ChevronsUpDown, LoaderCircle } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";

export interface OpcaoBusca {
  id: number;
  rotulo: string;
  detalhe?: string;
  desabilitado?: boolean;
}

/**
 * Seletor com busca no servidor (clientes, produtos…). `buscar` recebe o termo
 * com debounce e devolve as opções; `valor` é o id escolhido.
 */
export function BuscaCombobox({
  valor,
  rotuloSelecionado,
  buscar,
  chave,
  aoEscolher,
  placeholder = "Buscar…",
  vazio = "Nada encontrado.",
  className,
  id,
  invalido,
}: {
  valor: number | null;
  rotuloSelecionado?: string | null;
  buscar: (termo: string) => Promise<OpcaoBusca[]>;
  /** Prefixo da queryKey (ex.: "clientes"). */
  chave: string;
  aoEscolher: (opcao: OpcaoBusca | null) => void;
  placeholder?: string;
  vazio?: string;
  className?: string;
  id?: string;
  invalido?: boolean;
}) {
  const [aberto, setAberto] = useState(false);
  const [termo, setTermo] = useState("");
  const [termoDebounced, setTermoDebounced] = useState("");
  useEffect(() => {
    const t = window.setTimeout(() => setTermoDebounced(termo.trim()), 250);
    return () => window.clearTimeout(t);
  }, [termo]);

  const consulta = useQuery({
    queryKey: ["busca", chave, termoDebounced],
    queryFn: () => buscar(termoDebounced),
    enabled: aberto,
    staleTime: 30_000,
  });

  return (
    <Popover open={aberto} onOpenChange={setAberto}>
      <PopoverTrigger asChild>
        <Button
          id={id}
          type="button"
          variant="outline"
          role="combobox"
          aria-expanded={aberto}
          aria-invalid={invalido}
          className={cn("w-full justify-between font-normal", !valor && "text-muted-foreground", className)}
        >
          <span className="truncate">{valor ? rotuloSelecionado ?? `#${valor}` : placeholder}</span>
          <ChevronsUpDown className="size-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[var(--radix-popover-trigger-width)] min-w-72 p-0" align="start">
        <Command shouldFilter={false}>
          <CommandInput placeholder={placeholder} value={termo} onValueChange={setTermo} />
          <CommandList>
            {consulta.isFetching && (
              <div className="flex items-center gap-2 px-3 py-2 text-xs text-muted-foreground">
                <LoaderCircle className="size-3.5 animate-spin" /> buscando…
              </div>
            )}
            {!consulta.isFetching && consulta.data?.length === 0 && <CommandEmpty>{vazio}</CommandEmpty>}
            <CommandGroup>
              {consulta.data?.map((o) => (
                <CommandItem
                  key={o.id}
                  value={String(o.id)}
                  disabled={o.desabilitado}
                  onSelect={() => {
                    aoEscolher(o);
                    setAberto(false);
                  }}
                >
                  <Check className={cn("size-4", valor === o.id ? "opacity-100" : "opacity-0")} />
                  <div className="min-w-0 flex-1">
                    <div className="truncate">{o.rotulo}</div>
                    {o.detalhe && <div className="truncate text-xs text-muted-foreground">{o.detalhe}</div>}
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
