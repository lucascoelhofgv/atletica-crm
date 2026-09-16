import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, Boxes, LineChart, ShoppingBag, Users, type LucideIcon } from "lucide-react";

import { CabecalhoPagina } from "@/app/CabecalhoPagina";

export const Route = createFileRoute("/_auth/relatorios/")({
  component: PaginaRelatorios,
});

const RELATORIOS: {
  para: "/relatorios/vendas" | "/relatorios/produtos" | "/relatorios/estoque" | "/relatorios/clientes";
  titulo: string;
  descricao: string;
  icone: LucideIcon;
  usaPeriodo: boolean;
}[] = [
  {
    para: "/relatorios/vendas",
    titulo: "Vendas por período",
    descricao: "Receita e pedidos ao longo do tempo, por status e forma de pagamento.",
    icone: LineChart,
    usaPeriodo: true,
  },
  {
    para: "/relatorios/produtos",
    titulo: "Produtos vendidos",
    descricao: "Ranking de unidades e receita por produto no período.",
    icone: ShoppingBag,
    usaPeriodo: true,
  },
  {
    para: "/relatorios/estoque",
    titulo: "Estoque atual",
    descricao: "Saldo, mínimo e valor em estoque de cada produto, com alertas.",
    icone: Boxes,
    usaPeriodo: false,
  },
  {
    para: "/relatorios/clientes",
    titulo: "Clientes",
    descricao: "Quem mais compra: pedidos e valor gasto por cliente.",
    icone: Users,
    usaPeriodo: false,
  },
];

function PaginaRelatorios() {
  return (
    <div className="space-y-6">
      <CabecalhoPagina
        titulo="Relatórios"
        descricao="Todos exportam em CSV. Os que dependem de período usam o mesmo seletor do painel."
      />
      <div className="grid gap-4 sm:grid-cols-2">
        {RELATORIOS.map((r) => {
          const Icone = r.icone;
          return (
            <Link
              key={r.para}
              to={r.para}
              className="group flex items-start gap-4 rounded-xl border bg-card p-5 transition-colors hover:bg-accent"
            >
              <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Icone className="size-5" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 font-medium">
                  {r.titulo}
                  <ArrowRight className="size-4 opacity-0 transition-all group-hover:translate-x-0.5 group-hover:opacity-60" />
                </div>
                <p className="text-sm text-muted-foreground">{r.descricao}</p>
                <p className="mt-1 text-[11px] uppercase tracking-wide text-muted-foreground/70">
                  {r.usaPeriodo ? "por período" : "situação atual"}
                </p>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
