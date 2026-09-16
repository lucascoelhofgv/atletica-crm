import { Link } from "@tanstack/react-router";
import { ExternalLink } from "lucide-react";

import { useUsuario } from "@/features/auth/queries";
import { cn } from "@/lib/utils";

import { Marca } from "./Marca";
import { itensVisiveis, NAV_ADMIN, NAV_PRINCIPAL, type ItemNav } from "./nav";

const classeItem =
  "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-sidebar-foreground/75 transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground";
const classeAtivo =
  "bg-sidebar-accent text-sidebar-accent-foreground shadow-xs [&>svg:first-child]:text-sidebar-primary";

function Item({ item, aoNavegar }: { item: ItemNav; aoNavegar?: () => void }) {
  const Icone = item.icone;
  const conteudo = (
    <>
      <Icone className="size-4 shrink-0 opacity-80 group-hover:opacity-100" />
      <span className="truncate">{item.rotulo}</span>
      {item.externo && (
        <ExternalLink
          className="ml-auto size-3 opacity-0 transition-opacity group-hover:opacity-50"
          aria-label="abre fora do painel"
        />
      )}
    </>
  );

  if (item.rota) {
    return (
      <Link
        to={item.rota}
        className={classeItem}
        activeProps={{ className: cn(classeItem, classeAtivo) }}
        activeOptions={{ exact: item.rota === "/" }}
        onClick={aoNavegar}
      >
        {conteudo}
      </Link>
    );
  }
  // Link fora do SPA (admin do Django): navegação completa.
  return (
    <a href={item.externo} className={classeItem} title="Admin do Django">
      {conteudo}
    </a>
  );
}

export function Sidebar({ aoNavegar }: { aoNavegar?: () => void }) {
  const usuario = useUsuario();
  const principal = itensVisiveis(NAV_PRINCIPAL, usuario);
  const admin = itensVisiveis(NAV_ADMIN, usuario);

  return (
    <div className="flex h-full flex-col text-sidebar-foreground">
      <div className="flex h-14 items-center border-b border-sidebar-border px-4">
        <Link to="/" onClick={aoNavegar} className="min-w-0">
          <Marca />
        </Link>
      </div>

      <nav className="scroll-suave flex-1 space-y-6 overflow-y-auto px-3 py-4">
        <div className="space-y-0.5">
          {principal.map((item) => (
            <Item key={item.rotulo} item={item} aoNavegar={aoNavegar} />
          ))}
        </div>

        {admin.length > 0 && (
          <div>
            <div className="mb-1 px-3 text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/50">
              Administração
            </div>
            <div className="space-y-0.5">
              {admin.map((item) => (
                <Item key={item.rotulo} item={item} aoNavegar={aoNavegar} />
              ))}
            </div>
          </div>
        )}
      </nav>

      <div className="border-t border-sidebar-border px-4 py-3 text-[11px] text-sidebar-foreground/50">
        CRM Atlética Gorilada FGV
      </div>
    </div>
  );
}
