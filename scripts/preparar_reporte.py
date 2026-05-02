"""Prepara assets para el reporte LaTeX: figuras y tablas por escenario.

Salidas:
- `reports/figures/convergencia_<id>.png`
- `reports/figures/rutas_<id>.png`
- `reports/tables/rutas_<id>.tex`
- `reports/tables/resumen_global.tex`
- `reports/figures/boxplot_costos.png` (si lo generó analizar_resultados.py)

Uso:
    python scripts/preparar_reporte.py
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from memetico_cvrp.data import cargar_instancia
from memetico_cvrp.distance import calcular_matriz_distancias
from memetico_cvrp.metrics import cargar_agregados, tabla_resumen
from memetico_cvrp.plots import plot_convergencia, plot_rutas, tabla_rutas_a_latex, tabla_rutas_dataframe

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "results"
FIG_DIR = ROOT / "reports" / "figures"
TBL_DIR = ROOT / "reports" / "tables"

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("preparar_reporte")


def _historico_convergencia_por_seed(exp_id: str) -> tuple[list[list[float]], list[int]]:
    historicos: list[list[float]] = []
    seeds: list[int] = []
    for run_path in sorted((RESULTS / exp_id).glob("run_seed*.json")):
        data = json.loads(run_path.read_text(encoding="utf-8"))
        historicos.append(data["historico_convergencia"])
        seeds.append(data["meta"]["seed"])
    return historicos, seeds


def main() -> int:
    if not RESULTS.exists():
        log.error("No existe %s — corre primero `make experiments`.", RESULTS)
        return 1

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TBL_DIR.mkdir(parents=True, exist_ok=True)

    agregados = cargar_agregados(RESULTS)
    if not agregados:
        log.error("Sin agregados — corre `make experiments`.")
        return 1

    for exp_id, ag in agregados.items():
        nombre = ag.get("nombre", exp_id)
        instancia_path = ROOT / ag["instancia"]
        capacidad = int(ag["capacidad"])
        instancia = cargar_instancia(instancia_path, capacidad=capacidad)
        dist = calcular_matriz_distancias(instancia.nodos)

        # Convergencia.
        historicos, seeds = _historico_convergencia_por_seed(exp_id)
        if historicos:
            out_conv = FIG_DIR / f"convergencia_{exp_id}.png"
            plot_convergencia(
                historicos,
                titulo=f"Convergencia — {nombre} (N={instancia.num_clientes}, Q={capacidad})",
                output_path=out_conv,
                etiquetas_seeds=seeds,
            )
            log.info("✓ %s", out_conv.relative_to(ROOT))

        # Mejor run → rutas + tabla.
        mejor_path = RESULTS / exp_id / "mejor_run.json"
        if mejor_path.exists():
            mejor = json.loads(mejor_path.read_text(encoding="utf-8"))
            rutas = [list(r) for r in mejor["rutas"]]
            cargas = [int(c) for c in mejor["cargas"]]

            out_rutas = FIG_DIR / f"rutas_{exp_id}.png"
            plot_rutas(
                instancia.nodos,
                rutas,
                cargas,
                titulo=(
                    f"Mejor solución — {nombre} (seed {mejor['seed']}) — "
                    f"costo {mejor['costo_final']:.2f}"
                ),
                output_path=out_rutas,
                capacidad=capacidad,
            )
            log.info("✓ %s", out_rutas.relative_to(ROOT))

            filas = tabla_rutas_dataframe(rutas, cargas, capacidad, dist)
            tex = tabla_rutas_a_latex(filas, titulo=f"Rutas del mejor run — {nombre}")
            (TBL_DIR / f"rutas_{exp_id}.tex").write_text(tex + "\n", encoding="utf-8")
            log.info("✓ reports/tables/rutas_%s.tex", exp_id)

    # Tabla resumen global en LaTeX.
    filas = tabla_resumen(agregados)
    if filas:
        lineas = [
            "\\begin{table}[H]",
            "\\centering",
            "\\caption{Resumen de resultados por escenario}",
            "\\begin{tabular}{lrrrrrr}",
            "\\toprule",
            "Escenario & Mejor & Media & Std & Veh. (med.) & Útil.\\% & Tiempo (s) \\\\",
            "\\midrule",
        ]
        for f in filas:
            lineas.append(
                f"{f['nombre']} & {f['costo_mejor']:.2f} & {f['costo_media']:.2f} & "
                f"{f['costo_std']:.2f} & {f['vehiculos_media']:.1f} & "
                f"{f['utilizacion_pct']:.1f} & {f['tiempo_media_s']:.2f} \\\\"
            )
        lineas += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
        (TBL_DIR / "resumen_global.tex").write_text("\n".join(lineas) + "\n", encoding="utf-8")
        log.info("✓ reports/tables/resumen_global.tex")

    log.info("Assets de reporte preparados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
