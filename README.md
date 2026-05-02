# Algoritmo Memético para CVRP

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Build](https://img.shields.io/badge/build-WIP-lightgrey.svg)]()

**Maestría en Inteligencia Artificial y Analítica de Datos (MIAAD)** — Universidad Autónoma de Ciudad Juárez (UACJ)
**Materia:** Optimización Inteligente — Mtro. Raúl Gibrán Porras Alaniz
**Alumno:** Javier Augusto Rebull Saucedo (Matrícula 263483)
**Fecha:** mayo de 2026

---

> Implementación desde cero, sin librerías VRP externas, de un Algoritmo Memético que fusiona un Algoritmo Genético (exploración global) con Búsqueda Tabú (intensificación local) para resolver el Problema de Enrutamiento de Vehículos con Capacidad (CVRP). Tres escenarios de estrés, multi-seed, reporte LaTeX listo para Overleaf y publicación web Nuxt.

## Tabla de contenidos

- [Arranque rápido](#arranque-rápido)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Cómo correr experimentos](#cómo-correr-experimentos)
- [Cómo compilar el reporte](#cómo-compilar-el-reporte)
- [Cómo desplegar la web](#cómo-desplegar-la-web)
- [Resultados resumidos](#resultados-resumidos)
- [Referencias](#referencias)
- [Licencia](#licencia)

## Arranque rápido

```bash
# 1. Entorno Python
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Generar instancias y correr experimentos
make generate-data
make experiments

# 3. Construir figuras y assets
make report-assets
make web-data

# 4. Web (opcional)
npm install
npm run dev
```

## Estructura del proyecto

```
memeticoCVRP/
├── src/memetico_cvrp/         # Paquete Python principal
├── scripts/                   # Scripts de ejecución (generar, correr, analizar)
├── tests/                     # pytest
├── config/experiments.yaml    # Configuración versionada de experimentos
├── data/raw/                  # Instancias CSV + .meta.json
├── data/results/              # Resultados por experimento (multi-seed)
├── reports/                   # main.tex modular + sections/ + references.bib
├── components/, pages/        # Vue 3 / Nuxt 3
├── public/data/, public/images/   # Assets servidos por la web
├── Makefile                   # Pipeline reproducible
└── netlify.toml               # Despliegue estático
```

## Cómo correr experimentos

```bash
# Una sola vez
make generate-data

# Pipeline reproducible end-to-end
make ci
```

Las semillas, hiperparámetros y rutas viven en `config/experiments.yaml`. Cada run produce `data/results/<id>/run_seed<seed>.json` con metadatos de trazabilidad (commit hash, versiones, hash de instancia).

### Semillas oficiales

| Escenario  | N clientes | Q   | Semilla instancia | Semillas runs                  |
|------------|-----------:|----:|------------------:|--------------------------------|
| Base       | 25         | 50  | 2026              | 2026                           |
| Caso 1     | 50         | 100 | 20260201          | 2026, 2027, 2028, 2029, 2030   |
| Caso 2     | 100        | 30  | 20260202          | 2026, 2027, 2028, 2029, 2030   |
| Caso 3     | 75         | 200 | 20260203          | 2026, 2027, 2028, 2029, 2030   |

## Cómo compilar el reporte

El reporte vive en `reports/main.tex` y está modularizado en `reports/sections/`. **No se compila localmente** — se sube a [Overleaf](https://www.overleaf.com/) (subir la carpeta `reports/` completa o un zip) y allí se ejecuta `pdflatex` + `biber`.

## Cómo desplegar la web

`netlify.toml` ya está configurado. En Netlify:

1. Conectar el repo `jrebull/MIAAD_SmartOpti_memetic`.
2. Branch a desplegar: `main`.
3. Build command: `npm run generate` (ya configurado).
4. Publish directory: `.output/public`.

Localmente:

```bash
npm install
npm run dev          # desarrollo
npm run generate     # build estático
npm run preview      # previsualización
```

## Resultados resumidos

Campaña ejecutada el 2026-05-02 sobre macOS 25.5 / Python 3.14 (≈31 minutos totales en serie).

| Escenario                    | Mejor    | Media    | Std    | Vehíc. | Útil. % | Tiempo medio |
|------------------------------|---------:|---------:|-------:|-------:|--------:|-------------:|
| Caso 1 — Escala Media        |   705.05 |   763.17 |  42.15 |    6.0 |    91.3 |   30.07 s    |
| Caso 2 — Alta Densidad       |  3063.66 |  3099.86 |  18.21 |   38.0 |    89.7 |  310.66 s    |
| Caso 3 — Consolidación       |   951.52 |  1035.93 |  43.42 |    4.0 |    93.0 |   31.37 s    |

Observaciones:
- El **Caso 2** es ~10× más caro de calcular que los otros (5 minutos por seed) por la cantidad de rutas que la capacidad pequeña fuerza (38 vehículos), aunque su desviación estándar es la **menor** (18.21) porque casi cualquier solución razonable converge al mismo número de vehículos.
- El **Caso 3** alcanza 93 % de utilización con sólo 4 vehículos: cuando la capacidad es generosa, el algoritmo consolida con éxito.
- Todas las soluciones reportadas pasan el validador `feasibility.py` (cobertura única, capacidad respetada, costo recalculado coincide).

## Referencias

- Dantzig, G. B., & Ramser, J. H. (1959). *The Truck Dispatching Problem.* Management Science.
- Holland, J. H. (1975). *Adaptation in Natural and Artificial Systems.* University of Michigan Press.
- Glover, F. (1986). *Future paths for integer programming and links to artificial intelligence.* Computers & Operations Research.
- Moscato, P. (1989). *On Evolution, Search, Optimization, Genetic Algorithms and Martial Arts: Towards Memetic Algorithms.* Caltech.
- Talbi, E.-G. (2009). *Metaheuristics: From Design to Implementation.* Wiley.

Lista completa en `reports/references.bib`.

## Licencia

MIT — uso académico libre. Ver `LICENSE`.

---

_Javier Augusto Rebull Saucedo · Matrícula 263483 · MIAAD UACJ · Mayo 2026_
