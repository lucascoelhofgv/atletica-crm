/**
 * Capturas de tela do frontend (Chrome headless via puppeteer-core).
 *
 * Uso (com Django em :8010 e Vite em :5173 rodando):
 *   SESSAO=<sessionid> SAIDA=<pasta> node scripts/capturas.mjs
 *
 * O `sessionid` é gerado pelo Django (ver docs/INSTALACAO.md, seção
 * "Capturas de tela"), para não digitar senha em lugar nenhum.
 * Sem SESSAO, captura só a tela de login.
 */

import { mkdir } from "node:fs/promises";
import path from "node:path";

import puppeteer from "puppeteer-core";

const CHROME =
  process.env.CHROME ?? "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const BASE = process.env.BASE ?? "http://localhost:5173";
const SAIDA = process.env.SAIDA ?? path.resolve("capturas");
const SESSAO = process.env.SESSAO;

await mkdir(SAIDA, { recursive: true });

const navegador = await puppeteer.launch({
  executablePath: CHROME,
  headless: true,
  args: ["--no-sandbox", "--disable-gpu", "--hide-scrollbars"],
});

const erros = [];

async function pagina(largura, altura, mobile = false) {
  const p = await navegador.newPage();
  await p.setViewport({ width: largura, height: altura, deviceScaleFactor: 2, isMobile: mobile, hasTouch: mobile });
  p.on("pageerror", (e) => erros.push(`pageerror: ${e.message}`));
  p.on("console", (m) => {
    if (m.type() === "error") erros.push(`console: ${m.text()}`);
  });
  return p;
}

async function salvar(p, nome) {
  await p.evaluate(() => document.fonts.ready);
  await new Promise((r) => setTimeout(r, 400)); // animações de entrada
  const arquivo = path.join(SAIDA, `${nome}.png`);
  await p.screenshot({ path: arquivo, fullPage: false });
  console.log("salvo", arquivo);
}

async function definirTema(p, tema) {
  await p.evaluate((t) => localStorage.setItem("crm.tema", t), tema);
  await p.reload({ waitUntil: "networkidle0" });
}

// Modo por rotas: ROTAS="relatorios,relatorios/vendas?periodo=7d" captura
// só essas páginas (logado, tema escuro, viewport alto) e sai.
if (process.env.ROTAS && SESSAO) {
  const url = new URL(BASE);
  const cookie = { name: "sessionid", value: SESSAO, domain: url.hostname, path: "/", httpOnly: true };
  let n = 0;
  // Aceita "clientes" sem a barra inicial (o Git Bash converte "/clientes/..."
  // em caminho do Windows ao passar a variável para o Node).
  const rotas = process.env.ROTAS.split(",").map((r) => r.trim()).filter(Boolean).map((r) => `/${r.replace(/^\/+/, "")}`);
  for (const rota of rotas) {
    const p = await pagina(1440, 900);
    await p.setCookie(cookie);
    await p.goto(`${BASE}${rota}`, { waitUntil: "networkidle0" });
    await definirTema(p, process.env.TEMA ?? "dark");
    const alturaTotal = await p.evaluate(() => document.documentElement.scrollHeight);
    await p.setViewport({ width: 1440, height: Math.min(alturaTotal + 40, 4000), deviceScaleFactor: 2 });
    await p.evaluate(() => document.fonts.ready);
    await new Promise((r) => setTimeout(r, 1200));
    const nome = `${String(++n).padStart(2, "0")}-${rota.replace(/^\/app\/?/, "").replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "") || "painel"}`;
    await p.screenshot({ path: path.join(SAIDA, `${nome}.png`) });
    console.log("salvo", nome);
    await p.close();
  }
  await navegador.close();
  if (erros.length) {
    console.log("\nERROS NO NAVEGADOR:");
    for (const e of erros) console.log(" -", e);
    process.exitCode = 1;
  }
  process.exit();
}

// 1) Login (sem sessão)
{
  const p = await pagina(1440, 900);
  await p.goto(`${BASE}/`, { waitUntil: "networkidle0" });
  await salvar(p, "01-login-escuro");
  await definirTema(p, "light");
  await salvar(p, "02-login-claro");
  await p.close();
}

// 2) Área logada
if (SESSAO) {
  const url = new URL(BASE);
  const cookie = { name: "sessionid", value: SESSAO, domain: url.hostname, path: "/", httpOnly: true };

  const p = await pagina(1440, 900);
  await p.setCookie(cookie);
  await p.goto(`${BASE}/`, { waitUntil: "networkidle0" });
  await definirTema(p, "dark");
  await salvar(p, "03-painel-escuro");
  // Usa o botão real da topbar (testa o alternador, não só o localStorage).
  await p.click('button[aria-label="Usar tema claro"]');
  await salvar(p, "04-painel-claro");
  await p.close();

  // Página inteira, com comparação ligada e período longo (série mensal).
  // Viewport alto em vez de fullPage: o fullPage redimensiona na hora da foto
  // e reinicia a animação dos gráficos (barras saem vazias).
  const c = await pagina(1440, 900);
  await c.setCookie(cookie);
  await c.goto(`${BASE}/?periodo=semestre&comparar=true`, { waitUntil: "networkidle0" });
  await definirTema(c, "dark");
  const alturaTotal = await c.evaluate(() => document.documentElement.scrollHeight);
  await c.setViewport({ width: 1440, height: Math.min(alturaTotal + 40, 4000), deviceScaleFactor: 2 });
  await c.evaluate(() => document.fonts.ready);
  await new Promise((r) => setTimeout(r, 1200));
  await c.screenshot({ path: path.join(SAIDA, "07-painel-comparar-completo.png") });
  console.log("salvo 07-painel-comparar-completo.png");
  await c.close();

  const m = await pagina(390, 844, true);
  await m.setCookie(cookie);
  await m.goto(`${BASE}/`, { waitUntil: "networkidle0" });
  await m.evaluate(() => localStorage.setItem("crm.tema", "dark"));
  await m.reload({ waitUntil: "networkidle0" });
  await salvar(m, "05-painel-mobile");
  const botaoMenu = await m.$('button[aria-label="Abrir menu"]');
  if (botaoMenu) {
    await botaoMenu.click();
    await new Promise((r) => setTimeout(r, 500));
    await salvar(m, "06-painel-mobile-menu");
  }
  await m.close();
} else {
  console.log("SESSAO não informada: pulando telas logadas.");
}

await navegador.close();

if (erros.length) {
  console.log("\nERROS NO NAVEGADOR:");
  for (const e of erros) console.log(" -", e);
  process.exitCode = 1;
} else {
  console.log("\nSem erros de console/página.");
}
