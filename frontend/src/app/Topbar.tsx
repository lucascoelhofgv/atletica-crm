import { Menu, Moon, Sun } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { alternarTema, useTema } from "@/lib/tema";

import { BuscaGlobal } from "./BuscaGlobal";
import { MenuUsuario } from "./MenuUsuario";

export function Topbar({
  aoAbrirMenu,
  children,
}: {
  aoAbrirMenu: () => void;
  /** Conteúdo central (ex.: controle de período), definido pela página. */
  children?: React.ReactNode;
}) {
  const tema = useTema();

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-2 border-b bg-background/80 px-3 backdrop-blur sm:px-6">
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden"
        onClick={aoAbrirMenu}
        aria-label="Abrir menu"
      >
        <Menu />
      </Button>

      <div className="flex min-w-0 flex-1 items-center gap-2">{children ?? <BuscaGlobal />}</div>

      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            onClick={alternarTema}
            aria-label={tema === "dark" ? "Usar tema claro" : "Usar tema escuro"}
          >
            {tema === "dark" ? <Sun /> : <Moon />}
          </Button>
        </TooltipTrigger>
        <TooltipContent>{tema === "dark" ? "Tema claro" : "Tema escuro"}</TooltipContent>
      </Tooltip>

      <MenuUsuario />
    </header>
  );
}
