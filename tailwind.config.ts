import type { Config } from "tailwindcss";

export default {
  content: [
    "./components/**/*.{vue,js,ts}",
    "./pages/**/*.vue",
    "./app.vue",
    "./assets/**/*.{css,scss}",
  ],
  theme: {
    extend: {
      colors: {
        // Paleta sobria académica (alineada con HTML base del tutorial)
        ink: "#1A2130",
        mist: "#F5F7FA",
        graphite: "#5A72A0",
        sky: "#83B4FF",
      },
      fontFamily: {
        serif: ["Inter", "IBM Plex Serif", "Georgia", "serif"],
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica",
          "Arial",
          "sans-serif",
        ],
        mono: ["JetBrains Mono", "Fira Code", "Courier New", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
