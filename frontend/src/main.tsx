import "@/styles/globals.css";

import { QueryClientProvider } from "@tanstack/react-query";
import { createRouter, RouterProvider } from "@tanstack/react-router";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { definirAoNaoAutenticado } from "@/lib/api";
import { queryClient } from "@/lib/query-client";
import { inicializarTema } from "@/lib/tema";

import { routeTree } from "./routeTree.gen";

inicializarTema();

// O SPA atende a raiz; Django fica com /admin, /api, /conta/senha, recibo e estáticos.
export const router = createRouter({
  routeTree,
  context: { queryClient },
  defaultPreload: "intent",
  defaultPreloadStaleTime: 0,
  scrollRestoration: true,
});

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

// Sessão expirou no meio do uso: limpa o cache e volta ao login
// guardando a rota para retornar depois.
definirAoNaoAutenticado(() => {
  queryClient.clear();
  const atual = window.location.pathname + window.location.search;
  router.navigate({ to: "/login", search: { voltar: atual } });
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
);
