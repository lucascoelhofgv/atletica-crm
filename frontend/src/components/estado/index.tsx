import { AlertTriangle, Inbox, type LucideIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiErro } from "@/lib/api";
import { cn } from "@/lib/utils";

export function Vazio({
  icone: Icone = Inbox,
  titulo,
  descricao,
  acao,
  className,
}: {
  icone?: LucideIcon;
  titulo: string;
  descricao?: string;
  acao?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed px-6 py-12 text-center",
        className,
      )}
    >
      <Icone className="size-8 text-muted-foreground/60" />
      <div className="font-medium">{titulo}</div>
      {descricao && <p className="max-w-sm text-sm text-muted-foreground">{descricao}</p>}
      {acao && <div className="mt-2">{acao}</div>}
    </div>
  );
}

export function ErroCarregamento({
  erro,
  tentarDeNovo,
  className,
}: {
  erro: unknown;
  tentarDeNovo?: () => void;
  className?: string;
}) {
  const mensagem =
    erro instanceof ApiErro
      ? erro.message
      : erro instanceof Error
        ? erro.message
        : "Não foi possível carregar.";
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-2 rounded-xl border border-destructive/30 bg-destructive/5 px-6 py-10 text-center",
        className,
      )}
    >
      <AlertTriangle className="size-7 text-destructive" />
      <div className="font-medium">Algo deu errado</div>
      <p className="max-w-sm text-sm text-muted-foreground">{mensagem}</p>
      {tentarDeNovo && (
        <Button variant="outline" size="sm" className="mt-2" onClick={tentarDeNovo}>
          Tentar de novo
        </Button>
      )}
    </div>
  );
}

export function SkeletonCard({ className, linhas = 2 }: { className?: string; linhas?: number }) {
  return (
    <Card className={className}>
      <CardHeader>
        <Skeleton className="h-4 w-1/3" />
      </CardHeader>
      <CardContent className="space-y-2">
        <Skeleton className="h-8 w-1/2" />
        {Array.from({ length: linhas }).map((_, i) => (
          <Skeleton key={i} className="h-3 w-full" />
        ))}
      </CardContent>
    </Card>
  );
}

export function SkeletonLinhas({ n = 5, className }: { n?: number; className?: string }) {
  return (
    <div className={cn("space-y-2", className)}>
      {Array.from({ length: n }).map((_, i) => (
        <Skeleton key={i} className="h-9 w-full" />
      ))}
    </div>
  );
}

/** Tela inteira enquanto uma rota carrega (pendingComponent). */
export function PaginaCarregando() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-busy="true">
      {Array.from({ length: 4 }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
