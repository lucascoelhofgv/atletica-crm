/** Formatação pt-BR (moeda, números, datas). Usar sempre daqui, nunca inline. */

import { format, formatDistanceToNowStrict, isValid, parseISO } from "date-fns";
import { ptBR } from "date-fns/locale";

const moedaFmt = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const moedaCompactaFmt = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  notation: "compact",
  maximumFractionDigits: 1,
});
const numeroFmt = new Intl.NumberFormat("pt-BR");
const compactoFmt = new Intl.NumberFormat("pt-BR", { notation: "compact", maximumFractionDigits: 1 });
const percentualFmt = new Intl.NumberFormat("pt-BR", {
  style: "percent",
  maximumFractionDigits: 1,
  signDisplay: "exceptZero",
});

export const moeda = (v: number | string | null | undefined) => moedaFmt.format(Number(v ?? 0));
export const moedaCompacta = (v: number | string | null | undefined) =>
  moedaCompactaFmt.format(Number(v ?? 0));
export const numero = (v: number | string | null | undefined) => numeroFmt.format(Number(v ?? 0));
export const compacto = (v: number | string | null | undefined) => compactoFmt.format(Number(v ?? 0));
/** `variacao` em fração (0.12 = +12%). */
export const percentual = (v: number | null | undefined) =>
  v === null || v === undefined || !Number.isFinite(v) ? "—" : percentualFmt.format(v);

function paraData(valor: string | Date | null | undefined): Date | null {
  if (!valor) return null;
  const data = typeof valor === "string" ? parseISO(valor) : valor;
  return isValid(data) ? data : null;
}

export const data = (v: string | Date | null | undefined, padrao = "dd/MM/yyyy") => {
  const d = paraData(v);
  return d ? format(d, padrao, { locale: ptBR }) : "—";
};
export const dataHora = (v: string | Date | null | undefined) => data(v, "dd/MM/yyyy HH:mm");
export const dataCurta = (v: string | Date | null | undefined) => data(v, "d MMM");
export const mesAno = (v: string | Date | null | undefined) => data(v, "MMM/yy");
export const relativo = (v: string | Date | null | undefined) => {
  const d = paraData(v);
  return d ? formatDistanceToNowStrict(d, { addSuffix: true, locale: ptBR }) : "—";
};

export function iniciais(nome: string | null | undefined) {
  const partes = (nome ?? "").trim().split(/\s+/).filter(Boolean);
  if (partes.length === 0) return "?";
  return (partes[0][0] + (partes.length > 1 ? partes[partes.length - 1][0] : "")).toUpperCase();
}
