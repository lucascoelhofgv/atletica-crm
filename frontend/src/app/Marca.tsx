import { useQuery } from "@tanstack/react-query";

import { configQuery } from "@/features/config/api";
import { cn } from "@/lib/utils";

/** Logo oficial embarcado no build (public/marca). O admin pode trocar pela
 *  Configuracao; enquanto não trocar, este é o padrão. */
export const LOGO_PADRAO = `${import.meta.env.BASE_URL}marca/logo.png`;

/** Logo + nome da organização (white-label via /api/config/). */
export function Marca({
  compacta = false,
  className,
  tamanho = "md",
}: {
  compacta?: boolean;
  className?: string;
  tamanho?: "md" | "lg";
}) {
  const { data: cfg } = useQuery(configQuery);
  const nome = cfg?.nome_organizacao ?? "Atlética Gorilada FGV";
  const logo = cfg?.logo || LOGO_PADRAO;

  return (
    <div className={cn("flex items-center gap-3", className)}>
      <img
        src={logo}
        alt={nome}
        className={cn("shrink-0 object-contain", tamanho === "lg" ? "size-14" : "size-9")}
        draggable={false}
      />
      {!compacta && (
        <div className="min-w-0 leading-tight">
          <div
            className={cn(
              "truncate font-display font-semibold",
              tamanho === "lg" ? "text-lg" : "text-sm",
            )}
          >
            {nome}
          </div>
          <div className="truncate text-xs opacity-70">{cfg?.titulo_app ?? "CRM"}</div>
        </div>
      )}
    </div>
  );
}
