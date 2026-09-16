import { Star } from "lucide-react";

import { cn } from "@/lib/utils";

/** Exibe (ou, com `aoMudar`, edita) uma nota de 1 a 5. */
export function Estrelas({
  valor,
  aoMudar,
  tamanho = "size-4",
  className,
}: {
  valor: number;
  aoMudar?: (v: number) => void;
  tamanho?: string;
  className?: string;
}) {
  return (
    <span className={cn("inline-flex items-center gap-0.5", className)} role={aoMudar ? "radiogroup" : undefined}>
      {[1, 2, 3, 4, 5].map((n) => {
        const cheia = n <= Math.round(valor);
        const icone = <Star className={cn(tamanho, cheia ? "fill-primary text-primary" : "text-muted-foreground/40")} />;
        return aoMudar ? (
          <button key={n} type="button" onClick={() => aoMudar(n)} aria-label={`${n} de 5`} role="radio" aria-checked={n === valor} className="rounded hover:scale-110">
            {icone}
          </button>
        ) : (
          <span key={n}>{icone}</span>
        );
      })}
    </span>
  );
}
