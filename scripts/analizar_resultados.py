"""Análisis estadístico inter-escenarios.

Lee los `agregado.json` y `run_seed*.json` de `data/results/` y produce:
- `data/results/analisis_global.json` con métricas comparativas.
- `reports/figures/boxplot_costos.png` (también copiado a `public/images/`).

Uso:
    python scripts/analizar_resultados.py
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

import yaml

from memetico_cvrp.metrics import (
    cargar_agregados,
    comparar_costos_inter_escenarios,
    tabla_resumen,
)
from memetico_cvrp.plots import plot_boxplot_costos

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "results"
FIG_DIR = ROOT / "reports" / "figures"
PUBLIC_IMG = ROOT / "public" / "images"
PUBLIC_DATA = ROOT / "public" / "data"

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("analizar_resultados")


def _cargar_costos_por_run(exp_id: str) -> list[float]:
    """Lee todos los `run_seed*.json` del experimento y devuelve la lista de costos."""
    out: list[float] = []
    for run_path in sorted((RESULTS / exp_id).glob("run_seed*.json")):
        data = json.loads(run_path.read_text(encoding="utf-8"))
        out.append(float(data["costo_final"]))
    return out


def main() -> int:
    if not RESULTS.exists():
        log.error("No existe %s — corre primero `make experiments`.", RESULTS)
        return 1

    agregados = cargar_agregados(RESULTS)
    if not agregados:
        log.error("No hay agregados en %s — corre primero `make experiments`.", RESULTS)
        return 1

    log.info("Encontrados %d agregados: %s", len(agregados), list(agregados.keys()))

    # Tabla resumen y comparativos.
    filas = tabla_resumen(agregados)
    comparativo = comparar_costos_inter_escenarios(agregados)

    # Costos por run (para boxplot).
    costos_por_exp = {ag["nombre"]: _cargar_costos_por_run(exp_id)
                      for exp_id, ag in agregados.items()}

    if any(len(c) >= 2 for c in costos_por_exp.values()):
        FIG_DIR.mkdir(parents=True, exist_ok=True)
        boxplot_path = FIG_DIR / "boxplot_costos.png"
        plot_boxplot_costos(costos_por_exp, "Distribución de costos por escenario", boxplot_path)
        log.info("Boxplot generado en %s", boxplot_path.relative_to(ROOT))
        # Copiar a public/images para la web.
        PUBLIC_IMG.mkdir(parents=True, exist_ok=True)
        shutil.copy(boxplot_path, PUBLIC_IMG / boxplot_path.name)

    # Persistir análisis global.
    analisis = {
        "n_escenarios": len(agregados),
        "tabla_resumen": filas,
        "comparativo_inter_escenarios": comparativo,
        "costos_por_escenario": {k: v for k, v in costos_por_exp.items()},
    }
    out_path = RESULTS / "analisis_global.json"
    out_path.write_text(json.dumps(analisis, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    log.info("Análisis global escrito en %s", out_path.relative_to(ROOT))

    # También copiar a public/data para la web.
    PUBLIC_DATA.mkdir(parents=True, exist_ok=True)
    shutil.copy(out_path, PUBLIC_DATA / out_path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
