import { Link, type LinkProps } from "@tanstack/react-router";
import { ChevronLeft, Download } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/** Título + descrição + ações da página, com link de volta opcional. */
export function CabecalhoPagina({
  titulo,
  descricao,
  voltar,
  acoes,
  children,
  className,
}: {
  titulo: string;
  descricao?: React.ReactNode;
  /** Rota do SPA para o botão "voltar". */
  voltar?: { para: LinkProps["to"]; rotulo: string };
  acoes?: React.ReactNode;
  /** Linha extra abaixo (ex.: controle de período). */
  children?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("space-y-3", className)}>
      {voltar && (
        <Link
          to={voltar.para}
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
        >
          <ChevronLeft className="size-3.5" /> {voltar.rotulo}
        </Link>
      )}
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight">{titulo}</h1>
          {descricao && <p className="text-sm text-muted-foreground">{descricao}</p>}
        </div>
        {acoes && <div className="flex flex-wrap items-center gap-2">{acoes}</div>}
      </div>
      {children}
    </div>
  );
}

export function BotaoCsv({ href }: { href: string }) {
  return (
    <Button asChild variant="outline" size="sm">
      <a href={href} download>
        <Download /> Exportar CSV
      </a>
    </Button>
  );
}
