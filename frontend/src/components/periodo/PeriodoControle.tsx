import { format, parseISO } from "date-fns";
import { ptBR } from "date-fns/locale";
import { CalendarRange } from "lucide-react";
import { useState } from "react";
import type { DateRange } from "react-day-picker";

import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Label } from "@/components/ui/label";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Switch } from "@/components/ui/switch";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { PRESETS, usePeriodo } from "@/lib/periodo";
import { cn } from "@/lib/utils";

function rotuloIntervalo(inicio?: string, fim?: string) {
  if (!inicio || !fim) return "Personalizado";
  const a = parseISO(inicio);
  const b = parseISO(fim);
  const mesmoAno = a.getFullYear() === b.getFullYear();
  return `${format(a, mesmoAno ? "d MMM" : "d MMM yy", { locale: ptBR })} – ${format(b, "d MMM yy", { locale: ptBR })}`;
}

/**
 * Presets + intervalo personalizado + "comparar com período anterior".
 * Tudo vai para a URL (lib/periodo.ts); as queries reagem sozinhas.
 */
export function PeriodoControle({ className }: { className?: string }) {
  const { valores, definir } = usePeriodo();
  const [aberto, setAberto] = useState(false);
  const [intervalo, setIntervalo] = useState<DateRange | undefined>(() =>
    valores.inicio && valores.fim
      ? { from: parseISO(valores.inicio), to: parseISO(valores.fim) }
      : undefined,
  );

  function aplicar() {
    if (!intervalo?.from) return;
    const fim = intervalo.to ?? intervalo.from;
    definir({
      periodo: "custom",
      inicio: format(intervalo.from, "yyyy-MM-dd"),
      fim: format(fim, "yyyy-MM-dd"),
    });
    setAberto(false);
  }

  const custom = valores.periodo === "custom";

  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)}>
      <ToggleGroup
        type="single"
        variant="outline"
        size="sm"
        value={custom ? "" : valores.periodo}
        onValueChange={(v) => v && definir({ periodo: v as typeof valores.periodo })}
        aria-label="Período"
      >
        {PRESETS.map((p) => (
          <ToggleGroupItem key={p.chave} value={p.chave} className="px-3">
            {p.rotulo}
          </ToggleGroupItem>
        ))}
      </ToggleGroup>

      <Popover open={aberto} onOpenChange={setAberto}>
        <PopoverTrigger asChild>
          <Button
            variant={custom ? "secondary" : "outline"}
            size="sm"
            className={cn("gap-2", custom && "border-primary/50")}
          >
            <CalendarRange className="size-4" />
            {custom ? rotuloIntervalo(valores.inicio, valores.fim) : "Personalizado"}
          </Button>
        </PopoverTrigger>
        <PopoverContent align="end" className="w-auto p-0">
          <Calendar
            mode="range"
            numberOfMonths={2}
            locale={ptBR}
            selected={intervalo}
            onSelect={setIntervalo}
            defaultMonth={intervalo?.from}
            disabled={{ after: new Date() }}
          />
          <div className="flex items-center justify-between gap-2 border-t p-2">
            <span className="px-1 text-xs text-muted-foreground">
              {intervalo?.from
                ? rotuloIntervalo(
                    format(intervalo.from, "yyyy-MM-dd"),
                    format(intervalo.to ?? intervalo.from, "yyyy-MM-dd"),
                  )
                : "Escolha início e fim"}
            </span>
            <Button size="sm" onClick={aplicar} disabled={!intervalo?.from}>
              Aplicar
            </Button>
          </div>
        </PopoverContent>
      </Popover>

      <div className="flex items-center gap-2 pl-1">
        <Switch
          id="comparar"
          checked={valores.comparar}
          onCheckedChange={(v) => definir({ comparar: v })}
        />
        <Label htmlFor="comparar" className="cursor-pointer text-xs font-normal text-muted-foreground">
          Comparar com anterior
        </Label>
      </div>
    </div>
  );
}
