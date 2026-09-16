import type { QueryClient } from "@tanstack/react-query";
import { useQuery } from "@tanstack/react-query";
import { createRootRouteWithContext, Link, Outlet } from "@tanstack/react-router";
import { useEffect } from "react";
import { Toaster } from "sonner";

import { Button } from "@/components/ui/button";
import { TooltipProvider } from "@/components/ui/tooltip";
import { configQuery } from "@/features/config/api";
import { aplicarFavicon, aplicarMarca, useTema } from "@/lib/tema";

export interface ContextoRouter {
  queryClient: QueryClient;
}

export const Route = createRootRouteWithContext<ContextoRouter>()({
  component: Raiz,
  notFoundComponent: NaoEncontrado,
});

/** Aplica título, favicon e cores da Configuracao assim que ela chega. */
function EfeitoConfiguracao() {
  const { data: cfg } = useQuery(configQuery);
  useEffect(() => {
    if (!cfg) return;
    document.title = cfg.titulo_app || "CRM Atlética";
    aplicarFavicon(cfg.favicon);
    aplicarMarca(cfg);
  }, [cfg]);
  return null;
}

function Raiz() {
  const tema = useTema();
  return (
    <TooltipProvider delayDuration={300}>
      <EfeitoConfiguracao />
      <Outlet />
      <Toaster theme={tema} position="bottom-right" richColors closeButton />
    </TooltipProvider>
  );
}

function NaoEncontrado() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-3 p-6 text-center">
      <div className="font-display text-6xl font-semibold text-muted-foreground/40">404</div>
      <div className="text-lg font-medium">Página não encontrada</div>
      <p className="max-w-sm text-sm text-muted-foreground">
        O endereço pode ter mudado ou a tela ainda não foi migrada para o novo painel.
      </p>
      <Button asChild className="mt-2">
        <Link to="/">Ir para o painel</Link>
      </Button>
    </div>
  );
}
