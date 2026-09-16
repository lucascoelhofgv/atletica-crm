import { fileURLToPath, URL } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import { tanstackRouter } from "@tanstack/router-plugin/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Django em desenvolvimento (ver .claude/launch.json).
// changeOrigin: false é obrigatório: a forma abreviada ("/api": url) ativa
// changeOrigin e troca o Host, e aí o check de Origin do CSRF do Django falha.
const DJANGO = { target: "http://127.0.0.1:8010", changeOrigin: false };

export default defineConfig(({ command }) => ({
  // Em produção o Django serve o build em /static/app/ (WhiteNoise).
  base: command === "build" ? "/static/app/" : "/",
  plugins: [
    tanstackRouter({ target: "react", autoCodeSplitting: true }),
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  build: { outDir: "dist", emptyOutDir: true, sourcemap: false },
  server: {
    port: 5173,
    strictPort: true,
    // Mesma origem aparente: cookies de sessão/CSRF do Django funcionam.
    // Abrir por http://localhost:5173/ (não 127.0.0.1).
    proxy: {
      "/api": DJANGO,
      // Regex: só /admin e /admin/...; "/admin" simples casaria /administracao (rota do SPA).
      "^/admin(/|$)": DJANGO,
      "/static": DJANGO,
      "/media": DJANGO,
      "/conta": DJANGO,
      "^/pedidos/\\d+/recibo/": DJANGO,
    },
  },
}));
