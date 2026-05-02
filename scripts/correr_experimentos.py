"""Runner experimental multi-seed.

Lee `config/experiments.yaml`, ejecuta el algoritmo memético por cada
combinación (experimento, seed), persiste cada run con metadata completa
y produce el agregado estadístico por experimento.

Uso:
    python scripts/correr_experimentos.py
    python scripts/correr_experimentos.py --config config/experiments.yaml
    python scripts/correr_experimentos.py --solo caso_1 caso_3
    python scripts/correr_experimentos.py --verbose
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import traceback
from dataclasses import asdict
from pathlib import Path

import yaml

from memetico_cvrp.data import cargar_instancia
from memetico_cvrp.distance import calcular_matriz_distancias
from memetico_cvrp.feasibility import validar_solucion
from memetico_cvrp.io_utils import (
    calcular_agregado,
    cargar_run,
    dump_run,
    hash_md5,
    versiones_runtime,
)
from memetico_cvrp.memetic import ConfigMemetico, ResultadoMemetico, algoritmo_memetico

ROOT = Path(__file__).resolve().parents[1]


def _configurar_logging(verbose: bool, debug: bool) -> None:
    nivel = logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)
    logging.basicConfig(
        level=nivel,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _correr_un_experimento(exp: dict, results_root: Path) -> dict:
    """Ejecuta los N seeds de un experimento y devuelve agregado + resumen."""
    exp_id = exp["id"]
    nombre = exp["nombre"]
    instancia_path = ROOT / exp["instancia"]
    capacidad = int(exp["capacidad"])
    seeds = exp["seeds"]
    params = exp["parametros"]

    out_dir = results_root / exp_id
    out_dir.mkdir(parents=True, exist_ok=True)

    instancia = cargar_instancia(instancia_path, capacidad=capacidad)
    dist = calcular_matriz_distancias(instancia.nodos)

    print(
        f"\n=== Experimento {exp_id} — {nombre} === "
        f"N={instancia.num_clientes} Q={capacidad} "
        f"seeds={seeds} gen={params['generaciones']} pob={params['tamano_poblacion']}"
    )

    runs_completos: list[dict] = []
    fallos: list[dict] = []
    mejor_run: ResultadoMemetico | None = None
    mejor_seed: int | None = None

    for seed in seeds:
        cfg = ConfigMemetico(
            generaciones=int(params["generaciones"]),
            tamano_poblacion=int(params["tamano_poblacion"]),
            torneo_k=int(params["torneo_k"]),
            prob_tabu=float(params["prob_tabu"]),
            iter_tabu=int(params["iter_tabu"]),
            tenencia=int(params["tenencia"]),
            sample_size=int(params["sample_size"]),
            seed=int(seed),
            capacidad=capacidad,
            mutacion_prob=float(params.get("mutacion_prob", 0.0)),
        )

        t0 = time.perf_counter()
        try:
            resultado = algoritmo_memetico(instancia.nodos, cfg, dist=dist)
            # Validación blindada: si la solución no es factible, abortamos este run.
            validar_solucion(
                resultado.rutas,
                instancia.nodos,
                capacidad,
                distancia_reportada=resultado.costo_final,
                dist_matriz=dist,
            )
            dump_run(
                resultado,
                output_dir=out_dir,
                seed=int(seed),
                instancia_path=instancia_path,
            )
            run_data = cargar_run(out_dir / f"run_seed{seed}.json")
            runs_completos.append(run_data)
            print(
                f"  seed={seed:>5} | costo={resultado.costo_final:8.2f} | "
                f"vehículos={len(resultado.rutas):2d} | gen_mejor={resultado.generacion_mejor:3d} | "
                f"t={time.perf_counter() - t0:6.2f}s"
            )
            if mejor_run is None or resultado.costo_final < mejor_run.costo_final:
                mejor_run = resultado
                mejor_seed = int(seed)
        except Exception as exc:  # noqa: BLE001 — queremos seguir con los demás seeds
            tb = traceback.format_exc()
            fallos.append({"seed": int(seed), "error": str(exc), "traceback": tb})
            print(f"  seed={seed:>5} | FALLO: {exc}", file=sys.stderr)

    # Agregado estadístico.
    agregado = calcular_agregado(runs_completos, instancia_path, capacidad)
    agregado["experimento_id"] = exp_id
    agregado["nombre"] = nombre
    agregado["instancia"] = str(instancia_path.relative_to(ROOT))
    agregado["instancia_hash"] = hash_md5(instancia_path)
    agregado["capacidad"] = capacidad
    agregado["parametros"] = params
    agregado["fallos"] = fallos
    (out_dir / "agregado.json").write_text(
        json.dumps(agregado, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # Mejor run del experimento.
    if mejor_run is not None and mejor_seed is not None:
        mejor_data = {
            "seed": mejor_seed,
            "experimento_id": exp_id,
            "costo_final": float(mejor_run.costo_final),
            "num_vehiculos": len(mejor_run.rutas),
            "rutas": [list(r) for r in mejor_run.rutas],
            "cargas": [int(c) for c in mejor_run.cargas],
            "mejor_cromosoma": list(mejor_run.mejor_cromosoma),
            "configuracion": asdict(mejor_run.configuracion),
            "tiempo_ejecucion": float(mejor_run.tiempo_ejecucion),
            "generacion_mejor": int(mejor_run.generacion_mejor),
        }
        (out_dir / "mejor_run.json").write_text(
            json.dumps(mejor_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    return agregado


def main() -> int:
    parser = argparse.ArgumentParser(description="Runner experimental multi-seed CVRP.")
    parser.add_argument(
        "--config",
        default=str(ROOT / "config" / "experiments.yaml"),
        help="Ruta al YAML de experimentos.",
    )
    parser.add_argument(
        "--solo",
        nargs="*",
        help="Filtrar por IDs de experimento (default: todos).",
    )
    parser.add_argument(
        "--results",
        default=str(ROOT / "data" / "results"),
        help="Directorio raíz de resultados.",
    )
    parser.add_argument("--verbose", action="store_true", help="Logging INFO.")
    parser.add_argument("--debug", action="store_true", help="Logging DEBUG.")
    args = parser.parse_args()
    _configurar_logging(args.verbose, args.debug)

    config_path = Path(args.config)
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    experimentos = cfg["experimentos"]
    if args.solo:
        experimentos = [e for e in experimentos if e["id"] in set(args.solo)]
        if not experimentos:
            print(f"Ningún experimento coincide con --solo {args.solo}", file=sys.stderr)
            return 1

    results_root = Path(args.results)
    results_root.mkdir(parents=True, exist_ok=True)

    print(f"Versiones runtime: {versiones_runtime()}")
    inicio = time.perf_counter()
    agregados: list[dict] = []
    for exp in experimentos:
        agregados.append(_correr_un_experimento(exp, results_root))
    duracion = time.perf_counter() - inicio

    # Tabla resumen al final.
    print("\n" + "=" * 90)
    print(
        f"{'Escenario':<32} {'mejor':>10} {'media':>10} {'std':>8} "
        f"{'vehíc.':>7} {'útil%':>7} {'tiempo s':>10}"
    )
    print("-" * 90)
    for ag in agregados:
        c = ag.get("costo", {})
        v = ag.get("vehiculos", {})
        print(
            f"{ag['nombre'][:32]:<32} "
            f"{c.get('min', 0):>10.2f} {c.get('media', 0):>10.2f} {c.get('std', 0):>8.2f} "
            f"{v.get('media', 0):>7.1f} "
            f"{ag.get('utilizacion_promedio_pct', 0):>7.1f} "
            f"{ag.get('tiempo_segundos', {}).get('media', 0):>10.2f}"
        )
    print("=" * 90)
    print(f"Tiempo total de la campaña: {duracion:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
