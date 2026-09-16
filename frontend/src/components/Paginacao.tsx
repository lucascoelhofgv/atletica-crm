import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { numero } from "@/lib/formatos";

export function Paginacao({
  pagina,
  paginas,
  total,
  aoMudar,
  rotulo = "registros",
}: {
  pagina: number;
  paginas: number;
  total: number;
  aoMudar: (pagina: number) => void;
  rotulo?: string;
}) {
  if (total === 0) return null;
  return (
    <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
      <span>
        {numero(total)} {rotulo}
        {paginas > 1 && (
          <>
            {" · "}página {pagina} de {paginas}
          </>
        )}
      </span>
      {paginas > 1 && (
        <div className="flex items-center gap-1">
          <Button variant="outline" size="icon-sm" disabled={pagina <= 1} onClick={() => aoMudar(pagina - 1)} aria-label="Página anterior">
            <ChevronLeft />
          </Button>
          <Button variant="outline" size="icon-sm" disabled={pagina >= paginas} onClick={() => aoMudar(pagina + 1)} aria-label="Próxima página">
            <ChevronRight />
          </Button>
        </div>
      )}
    </div>
  );
}
