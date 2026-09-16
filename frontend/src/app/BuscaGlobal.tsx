import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { Search } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { api } from "@/lib/api";

interface Grupo {
  grupo: string;
  rotulo: string;
  itens: { id: number; titulo: string; detalhe: string; url: string }[];
}

/** Busca global (Ctrl+K): clientes, produtos, pedidos, fornecedores, tarefas, membros. */
export function BuscaGlobal() {
  const [aberto, setAberto] = useState(false);
  const [termo, setTermo] = useState("");
  const [termoDebounced, setTermoDebounced] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const t = window.setTimeout(() => setTermoDebounced(termo.trim()), 200);
    return () => window.clearTimeout(t);
  }, [termo]);

  useEffect(() => {
    function atalho(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setAberto((a) => !a);
      }
    }
    document.addEventListener("keydown", atalho);
    return () => document.removeEventListener("keydown", atalho);
  }, []);

  const consulta = useQuery({
    queryKey: ["busca-global", termoDebounced],
    queryFn: () => api<{ grupos: Grupo[] }>("busca/", { params: { q: termoDebounced } }),
    enabled: aberto && termoDebounced.length >= 2,
    staleTime: 30_000,
  });

  function ir(url: string) {
    setAberto(false);
    setTermo("");
    void navigate({ to: url as never });
  }

  return (
    <>
      <Button variant="outline" size="sm" className="h-8 w-full max-w-xs justify-start gap-2 text-muted-foreground sm:w-64" onClick={() => setAberto(true)}>
        <Search className="size-4" />
        <span className="flex-1 text-left text-xs">Buscar…</span>
        <kbd className="hidden rounded border bg-muted px-1.5 font-mono text-[10px] sm:inline">Ctrl K</kbd>
      </Button>
      <CommandDialog open={aberto} onOpenChange={setAberto} title="Busca" description="Clientes, produtos, pedidos, fornecedores, tarefas e membros">
        <CommandInput placeholder="Digite pelo menos 2 letras…" value={termo} onValueChange={setTermo} />
        <CommandList>
          {termoDebounced.length < 2 && <div className="px-3 py-6 text-center text-xs text-muted-foreground">Busque por nome, número do pedido, SKU, e-mail…</div>}
          {consulta.isFetching && <div className="px-3 py-2 text-xs text-muted-foreground">buscando…</div>}
          {consulta.data && consulta.data.grupos.length === 0 && !consulta.isFetching && <CommandEmpty>Nada encontrado.</CommandEmpty>}
          {consulta.data?.grupos.map((g) => (
            <CommandGroup key={g.grupo} heading={g.rotulo}>
              {g.itens.map((i) => (
                <CommandItem key={`${g.grupo}-${i.id}`} value={`${g.grupo}-${i.id}-${i.titulo}`} onSelect={() => ir(i.url)}>
                  <div className="min-w-0 flex-1">
                    <div className="truncate">{i.titulo}</div>
                    {i.detalhe && <div className="truncate text-xs text-muted-foreground">{i.detalhe}</div>}
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>
          ))}
        </CommandList>
      </CommandDialog>
    </>
  );
}
