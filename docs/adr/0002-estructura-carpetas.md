# ADR 0002 — Estructura de carpetas (Nuxt en raíz, LaTeX en `reports/`)

**Fecha:** 2026-05-02
**Estado:** Aceptado

## Contexto

El proyecto previo (`EstrategiasEvolutivas/`) puso el sitio Nuxt en `web/` y el reporte LaTeX en `LaTeX/`. El plan brutal de este proyecto (`Prompts/PLAN_BRUTAL_USER_STORIES_MEMETICO_CVRP.md`) especifica una estructura distinta:

- Nuxt en la **raíz** (`nuxt.config.ts`, `package.json`, `app.vue`, `assets/`, `components/`, `pages/`, `public/`).
- Reporte LaTeX en **`reports/`** (`main.tex`, `sections/`, `tables/`, `figures/`, `references.bib`).

## Decisión

Seguir el plan brutal. La raíz hospeda Nuxt; el reporte vive en `reports/`.

## Consecuencias

- `netlify.toml` apunta a `.output/public` desde la raíz (no requiere `cd web`).
- Coexisten en raíz: paquete Python (`src/memetico_cvrp/`), Makefile, scripts/, configuración Python (`pyproject.toml`, `requirements.txt`) y configuración Node (`package.json`, `nuxt.config.ts`, `tailwind.config.ts`, `tsconfig.json`).
- Se evita confusión sobre qué archivos son la fuente de la web vs el paquete Python por el `pyproject.toml` (que limita el paquete a `src/`).
- El `.gitignore` cubre tanto artefactos Python (`.venv`, `__pycache__`, `.pytest_cache`) como Node (`node_modules`, `.nuxt`, `.output`).
