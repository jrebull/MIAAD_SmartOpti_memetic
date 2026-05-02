"""Genera las cuatro instancias oficiales (1 base + 3 escenarios) con un solo comando.

Las semillas son las pactadas en el plan brutal:
- Base tutorial : seed=2026,     N=25,  Q=50
- Caso 1        : seed=20260201, N=50,  Q=100  (Escala Media)
- Caso 2        : seed=20260202, N=100, Q=30   (Alta Densidad / Rutas Cortas)
- Caso 3        : seed=20260203, N=75,  Q=200  (Rutas de Consolidación)

Ejecutar desde la raíz del repo:
    python scripts/generar_instancias.py
"""

from __future__ import annotations

import logging
from pathlib import Path

from memetico_cvrp.data import cargar_instancia, generar_instancia_cvrp

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("generar_instancias")

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"


INSTANCIAS = [
    {
        "nombre": "base_tutorial",
        "filename": "instancia_base_25_q50.csv",
        "num_clientes": 25,
        "capacidad": 50,
        "seed": 2026,
    },
    {
        "nombre": "caso_1_escala_media",
        "filename": "caso_1_50_clientes_q100.csv",
        "num_clientes": 50,
        "capacidad": 100,
        "seed": 20260201,
    },
    {
        "nombre": "caso_2_alta_densidad",
        "filename": "caso_2_100_clientes_q30.csv",
        "num_clientes": 100,
        "capacidad": 30,
        "seed": 20260202,
    },
    {
        "nombre": "caso_3_consolidacion",
        "filename": "caso_3_75_clientes_q200.csv",
        "num_clientes": 75,
        "capacidad": 200,
        "seed": 20260203,
    },
]


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    log.info("Generando instancias en %s", RAW_DIR)
    log.info("-" * 70)

    for cfg in INSTANCIAS:
        out = RAW_DIR / cfg["filename"]
        generar_instancia_cvrp(
            num_clientes=cfg["num_clientes"],
            capacidad=cfg["capacidad"],
            seed=cfg["seed"],
            output_path=out,
            nombre_escenario=cfg["nombre"],
        )
        ins = cargar_instancia(out)
        suma = sum(n.demanda for n in ins.nodos.values())
        log.info(
            "%-30s N=%3d  Q=%3d  seed=%d  demanda_total=%d  archivo=%s",
            cfg["nombre"],
            ins.num_clientes,
            ins.capacidad,
            cfg["seed"],
            suma,
            out.name,
        )

    log.info("-" * 70)
    log.info("Listo: %d instancias generadas con su .meta.json", len(INSTANCIAS))


if __name__ == "__main__":
    main()
