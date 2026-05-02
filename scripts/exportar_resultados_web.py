"""Exporta JSON e imágenes al directorio público de la web Nuxt.

Salidas:
- `public/data/resumen_experimentos.json` (consumido por la home)
- `public/data/<exp_id>.json` (datos detallados por escenario)
- `public/images/convergencia_<id>.png`
- `public/images/rutas_<id>.png`
- `public/images/boxplot_costos.png` si existe

Uso:
    python scripts/exportar_resultados_web.py
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

from memetico_cvrp.metrics import cargar_agregados, tabla_resumen

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "results"
FIG_DIR = ROOT / "reports" / "figures"
PUBLIC_DATA = ROOT / "public" / "data"
PUBLIC_IMG = ROOT / "public" / "images"
ASSETS_DATA = ROOT / "assets" / "data"  # copia inlinable durante el build Vite

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("exportar_web")


def main() -> int:
    if not RESULTS.exists():
        log.warning("No existe %s — la web mostrará 'sin resultados'.", RESULTS)
        return 0

    PUBLIC_DATA.mkdir(parents=True, exist_ok=True)
    PUBLIC_IMG.mkdir(parents=True, exist_ok=True)
    ASSETS_DATA.mkdir(parents=True, exist_ok=True)

    agregados = cargar_agregados(RESULTS)
    if not agregados:
        log.warning("No hay agregados — la web mostrará 'sin resultados'.")
        return 0

    filas = tabla_resumen(agregados)
    resumen = {
        "n_escenarios": len(agregados),
        "escenarios": filas,
    }
    payload = json.dumps(resumen, indent=2, ensure_ascii=False) + "\n"
    (PUBLIC_DATA / "resumen_experimentos.json").write_text(payload, encoding="utf-8")
    (ASSETS_DATA / "resumen_experimentos.json").write_text(payload, encoding="utf-8")
    log.info("✓ resumen_experimentos.json (public + assets)")

    for exp_id, ag in agregados.items():
        # Detalle por escenario para la página individual.
        detalle = {
            "id": exp_id,
            "nombre": ag.get("nombre", exp_id),
            "instancia": ag.get("instancia"),
            "capacidad": ag.get("capacidad"),
            "n_runs": ag.get("n_runs"),
            "costo": ag.get("costo"),
            "vehiculos": ag.get("vehiculos"),
            "tiempo_segundos": ag.get("tiempo_segundos"),
            "utilizacion_promedio_pct": ag.get("utilizacion_promedio_pct"),
            "parametros": ag.get("parametros"),
            "demanda_total_instancia": ag.get("demanda_total_instancia"),
        }
        # Mejor solución detallada.
        mejor = RESULTS / exp_id / "mejor_run.json"
        if mejor.exists():
            detalle["mejor_run"] = json.loads(mejor.read_text(encoding="utf-8"))
        payload_exp = json.dumps(detalle, indent=2, ensure_ascii=False) + "\n"
        (PUBLIC_DATA / f"{exp_id}.json").write_text(payload_exp, encoding="utf-8")
        (ASSETS_DATA / f"{exp_id}.json").write_text(payload_exp, encoding="utf-8")
        log.info("✓ %s.json (public + assets)", exp_id)

    # Imágenes (las copiadas, todas opcionales según existan).
    for img_name in [
        *[f"convergencia_{k}.png" for k in agregados],
        *[f"rutas_{k}.png" for k in agregados],
        "boxplot_costos.png",
    ]:
        src = FIG_DIR / img_name
        if src.exists():
            shutil.copy(src, PUBLIC_IMG / img_name)
            log.info("✓ public/images/%s", img_name)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
