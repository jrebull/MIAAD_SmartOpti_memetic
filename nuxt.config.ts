// Configuración Nuxt 3 — sitio estático para Netlify
export default defineNuxtConfig({
  compatibilityDate: "2026-05-01",
  devtools: { enabled: true },
  modules: ["@nuxtjs/tailwindcss"],
  css: ["~/assets/css/main.css"],
  ssr: true,
  nitro: {
    preset: "static",
    prerender: {
      // Rutas dinámicas /escenarios/[id] no se descubren por crawl si no hay link
      // estático en otra página crawleable. Las declaramos explícitamente para
      // que Netlify sirva HTML estático en visitas directas.
      routes: [
        "/escenarios/caso_1",
        "/escenarios/caso_2",
        "/escenarios/caso_3",
        "/playground",
      ],
      crawlLinks: true,
    },
  },
  app: {
    head: {
      htmlAttrs: { lang: "es" },
      title: "Algoritmo Memético CVRP — MIAAD UACJ",
      meta: [
        { charset: "utf-8" },
        { name: "viewport", content: "width=device-width, initial-scale=1" },
        {
          name: "description",
          content:
            "Implementación desde cero de un Algoritmo Memético (GA + Búsqueda Tabú) para CVRP. MIAAD — Universidad Autónoma de Ciudad Juárez. Mayo 2026.",
        },
        { property: "og:title", content: "Algoritmo Memético CVRP — MIAAD UACJ" },
        {
          property: "og:description",
          content:
            "Resultados de tres escenarios CVRP resueltos con Algoritmo Memético GA+Tabú.",
        },
        { property: "og:type", content: "website" },
      ],
      link: [{ rel: "icon", type: "image/svg+xml", href: "/favicon.svg" }],
    },
  },
});
