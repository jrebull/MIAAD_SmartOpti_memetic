"""Sincroniza el paquete `memetico_cvrp` a `public/playground/` para Pyodide.

Pyodide carga el código Python en el navegador. Para no duplicar la lógica,
mantenemos `src/memetico_cvrp/` como única fuente de verdad y este script
copia los `.py` críticos al directorio público que el sitio Nuxt sirve.

También copia la instancia base CSV (N=25, Q=50) que el playground usa.

Uso:
    python scripts/preparar_playground.py
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_PKG = ROOT / "src" / "memetico_cvrp"
DEST_PKG = ROOT / "public" / "playground" / "memetico_cvrp"
ASSETS_CODIGO = ROOT / "assets" / "codigo"  # para import estático en /codigo
INSTANCIA_CSV_SRC = ROOT / "data" / "raw" / "instancia_base_25_q50.csv"
INSTANCIA_CSV_DEST = ROOT / "public" / "playground" / "instancia_base_25_q50.csv"

# Archivos del paquete que Pyodide necesita. Excluimos plots.py (matplotlib),
# metrics.py (no se usa en el playground) e io_utils.py (filesystem-bound).
ARCHIVOS = [
    "__init__.py",
    "data.py",
    "distance.py",
    "split.py",
    "genetic.py",
    "tabu.py",
    "memetic.py",
    "feasibility.py",
]

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("preparar_playground")


def main() -> int:
    DEST_PKG.mkdir(parents=True, exist_ok=True)
    ASSETS_CODIGO.mkdir(parents=True, exist_ok=True)

    for nombre in ARCHIVOS:
        src = SRC_PKG / nombre
        dst = DEST_PKG / nombre
        if not src.exists():
            log.error("Falta %s", src)
            return 1
        shutil.copy(src, dst)
        # Copia espejo a assets/codigo/ para que la página /codigo
        # haga import estático (?raw) durante el build de Vite.
        if nombre != "__init__.py":
            shutil.copy(src, ASSETS_CODIGO / nombre)
        log.info("✓ %s", dst.relative_to(ROOT))

    if not INSTANCIA_CSV_SRC.exists():
        log.error("Falta %s — corre `make generate-data` primero.", INSTANCIA_CSV_SRC)
        return 1
    shutil.copy(INSTANCIA_CSV_SRC, INSTANCIA_CSV_DEST)
    log.info("✓ %s", INSTANCIA_CSV_DEST.relative_to(ROOT))

    # El runner.py se mantiene escrito a mano (no se sobrescribe).
    runner = ROOT / "public" / "playground" / "runner.py"
    if not runner.exists():
        log.warning("⚠ %s no existe — el playground no funcionará sin él.",
                    runner.relative_to(ROOT))
    else:
        log.info("✓ %s (mantenido)", runner.relative_to(ROOT))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
