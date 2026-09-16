import type { LinkProps } from "@tanstack/react-router";
import {
  BarChart3,
  Boxes,
  CalendarDays,
  CheckSquare,
  Clock,
  FileSpreadsheet,
  Import,
  KeyRound,
  LayoutDashboard,
  Palette,
  Receipt,
  Shield,
  Truck,
  UserCog,
  Users,
  Wrench,
  type LucideIcon,
} from "lucide-react";

import type { Modulo, Usuario } from "@/features/auth/types";

export interface ItemNav {
  rotulo: string;
  icone: LucideIcon;
  /** Rota do SPA (quando o módulo já foi migrado). */
  rota?: LinkProps["to"];
  /** Link externo ao SPA (ex.: admin do Django). */
  externo?: string;
  /** Some da navegação se o usuário não pode ler o módulo. */
  modulo?: Modulo;
  somenteAdmin?: boolean;
}

export const NAV_PRINCIPAL: ItemNav[] = [
  { rotulo: "Painel", icone: LayoutDashboard, rota: "/" },
  { rotulo: "Clientes", icone: Users, rota: "/clientes", modulo: "crm" },
  { rotulo: "Produtos e estoque", icone: Boxes, rota: "/produtos", modulo: "catalogo" },
  { rotulo: "Pedidos", icone: Receipt, rota: "/pedidos", modulo: "vendas" },
  { rotulo: "Fornecedores", icone: Truck, rota: "/fornecedores", modulo: "fornecedores" },
  { rotulo: "Tarefas", icone: CheckSquare, rota: "/tarefas", modulo: "tarefas" },
  { rotulo: "Eventos e festas", icone: CalendarDays, rota: "/eventos", modulo: "eventos" },
  { rotulo: "Relatórios", icone: BarChart3, rota: "/relatorios", modulo: "relatorios" },
];

export const NAV_ADMIN: ItemNav[] = [
  { rotulo: "Membros", icone: UserCog, rota: "/administracao/membros", modulo: "membros" },
  { rotulo: "Identidade visual", icone: Palette, rota: "/administracao/configuracao", somenteAdmin: true },
  { rotulo: "Histórico", icone: Clock, rota: "/administracao/historico", somenteAdmin: true },
  { rotulo: "Acessos", icone: KeyRound, rota: "/administracao/acessos", somenteAdmin: true },
  { rotulo: "Google Sheets", icone: FileSpreadsheet, rota: "/administracao/sheets", somenteAdmin: true },
  { rotulo: "Importar de planilha", icone: Import, rota: "/administracao/importar", somenteAdmin: true },
  { rotulo: "Admin avançado", icone: Wrench, externo: "/admin/", somenteAdmin: true },
];

export const ICONE_MARCA = Shield;

export function itensVisiveis(itens: ItemNav[], usuario: Usuario) {
  return itens.filter((item) => {
    if (item.somenteAdmin && !usuario.eh_admin) return false;
    if (item.modulo && !usuario.permissoes[item.modulo]?.ler) return false;
    return true;
  });
}
