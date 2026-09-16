import { createFileRoute, Outlet, redirect, retainSearchParams } from "@tanstack/react-router";

import { AppShell } from "@/app/AppShell";
import { PaginaCarregando } from "@/components/estado";
import { usuarioAtualQuery } from "@/features/auth/queries";
import { CHAVES_PERIODO, periodoSearchSchema } from "@/lib/periodo";

/**
 * Layout protegido: tudo sob `/_auth` exige sessão. Sem sessão, vai para o
 * login guardando a rota atual em `voltar`.
 *
 * O período de análise (?periodo=...&comparar=true) é validado aqui e
 * preservado ao navegar entre telas (retainSearchParams).
 */
export const Route = createFileRoute("/_auth")({
  validateSearch: periodoSearchSchema,
  search: { middlewares: [retainSearchParams([...CHAVES_PERIODO])] },
  beforeLoad: async ({ context, location }) => {
    const usuario = await context.queryClient.ensureQueryData(usuarioAtualQuery);
    if (!usuario) {
      throw redirect({ to: "/login", search: { voltar: location.href } });
    }
    return { usuario };
  },
  pendingComponent: PaginaCarregando,
  component: () => (
    <AppShell>
      <Outlet />
    </AppShell>
  ),
});
