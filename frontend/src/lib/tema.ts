/**
 * Tema claro/escuro e tokens de marca.
 *
 * O app nasce escuro (`<html class="dark">` no index.html). A escolha do
 * usuário fica em localStorage, só como conveniência por navegador.
 */

import { useSyncExternalStore } from "react";

export type Tema = "dark" | "light";

const CHAVE = "crm.tema";
const ouvintes = new Set<() => void>();

function lerSalvo(): Tema | null {
  try {
    const valor = localStorage.getItem(CHAVE);
    return valor === "dark" || valor === "light" ? valor : null;
  } catch {
    return null;
  }
}

export function temaAtual(): Tema {
  return document.documentElement.classList.contains("dark") ? "dark" : "light";
}

export function aplicarTema(tema: Tema, persistir = true) {
  document.documentElement.classList.toggle("dark", tema === "dark");
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute("content", tema === "dark" ? "#0b0f19" : "#f7f8fb");
  if (persistir) {
    try {
      localStorage.setItem(CHAVE, tema);
    } catch {
      /* navegação privada: ignora */
    }
  }
  ouvintes.forEach((fn) => fn());
}

export function inicializarTema() {
  aplicarTema(lerSalvo() ?? "dark", false);
}

export function alternarTema() {
  aplicarTema(temaAtual() === "dark" ? "light" : "dark");
}

export function useTema(): Tema {
  return useSyncExternalStore(
    (fn) => {
      ouvintes.add(fn);
      return () => ouvintes.delete(fn);
    },
    temaAtual,
    () => "dark",
  );
}

/** Cores da Configuracao (white-label) viram tokens de marca em runtime. */
export function aplicarMarca(cfg: { cor_primaria?: string | null; cor_secundaria?: string | null }) {
  const raiz = document.documentElement.style;
  if (cfg.cor_primaria) raiz.setProperty("--brand-primary", cfg.cor_primaria);
  if (cfg.cor_secundaria) raiz.setProperty("--brand-secondary", cfg.cor_secundaria);
}

export function aplicarFavicon(url: string | null | undefined) {
  if (!url) return;
  let link = document.querySelector<HTMLLinkElement>('link[rel="icon"]');
  if (!link) {
    link = document.createElement("link");
    link.rel = "icon";
    document.head.appendChild(link);
  }
  link.href = url;
}
