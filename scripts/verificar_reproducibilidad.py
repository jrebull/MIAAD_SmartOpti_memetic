"""Verifica reproducibilidad bit-a-bit del pipeline experimental.

Estrategia "smoke":
1. Genera de nuevo las 4 instancias y compara MD5 contra `.meta.json` previo.
2. Por cada experimento, recorre los `run_seed*.json` y reproduce un subconjunto
   de seeds con generaciones reducidas; compara que el costo final del run
   reproducido sea idéntico al persistido (con tolerancia float).
3. Construye `data/results/MANIFEST.json` consolidado con hashes y versiones.

Uso:
    python scripts/verificar_reproducibilidad.py [--seeds-por-exp 1] [--escribir-manifest]
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from memetico_cvrp.data import cargar_instancia, generar_instancia_cvrp
from memetico_cvrp.distance import calcular_matriz_distancias
from memetico_cvrp.io_utils import (
    git_commit_hash,
    hash_md5,
    versiones_runtime,
)
from memetico_cvrp.memetic import ConfigMemetico, algoritmo_memetico

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RESULTS = ROOT / "data" / "results"

# Misma lista que en scripts/generar_instancias.py
INSTANCIAS_OFICIALES = [
    {"filename": "instancia_base_25_q50.csv",     "num_clientes": 25,  "capacidad": 50,  "seed": 2026,     "nombre": "base_tutorial"},
    {"filename": "caso_1_50_clientes_q100.csv",   "num_clientes": 50,  "capacidad": 100, "seed": 20260201, "nombre": "caso_1_escala_media"},
    {"filename": "caso_2_100_clientes_q30.csv",   "num_clientes": 100, "capacidad": 30,  "seed": 20260202, "nombre": "caso_2_alta_densidad"},
    {"filename": "caso_3_75_clientes_q200.csv",   "num_clientes": 75,  "capacidad": 200, "seed": 20260203, "nombre": "caso_3_consolidacion"},
]


logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("verificar_reproducibilidad")


def _verificar_instancias() -> tuple[bool, list[dict]]:
    """Regenera cada instancia oficial en /tmp y compara MD5 con la versionada."""
    import tempfile

    todo_ok = True
    detalles: list[dict] = []
    for cfg in INSTANCIAS_OFICIALES:
        archivo = RAW / cfg["filename"]
        if not archivo.exists():
            log.error("Falta instancia versionada: %s", archivo)
            todo_ok = False
            continue
        with tempfile.TemporaryDirectory() as td:
            tmp_csv = Path(td) / cfg["filename"]
            generar_instancia_cvrp(
                num_clientes=cfg["num_clientes"],
                capacidad=cfg["capacidad"],
                seed=cfg["seed"],
                output_path=tmp_csv,
                nombre_escenario=cfg["nombre"],
            )
            md5_actual = hash_md5(archivo)
            md5_regen = hash_md5(tmp_csv)
            ok = md5_actual == md5_regen
            todo_ok = todo_ok and ok
            estado = "OK" if ok else "FALLO"
            log.info("%s instancia %s: md5=%s", estado, cfg["filename"], md5_actual)
            detalles.append({
                "filename": cfg["filename"],
                "md5_versionada": md5_actual,
                "md5_regenerada": md5_regen,
                "ok": ok,
            })
    return todo_ok, detalles


def _verificar_runs(seeds_por_exp: int, tolerancia: float) -> tuple[bool, list[dict]]:
    """Por cada experimento, reproduce los primeros N seeds y compara el costo."""
    todo_ok = True
    detalles: list[dict] = []
    if not RESULTS.exists():
        log.warning("No existe %s — sin runs que verificar.", RESULTS)
        return True, []

    for exp_dir in sorted(p for p in RESULTS.iterdir() if p.is_dir()):
        runs = sorted(exp_dir.glob("run_seed*.json"))
        if not runs:
            continue
        log.info("Experimento %s — %d runs persistidos.", exp_dir.name, len(runs))
        for run_path in runs[:seeds_por_exp]:
            data = json.loads(run_path.read_text(encoding="utf-8"))
            cfg = ConfigMemetico(**data["configuracion"])
            instancia_path = ROOT / data["instancia_path"]
            if not instancia_path.exists():
                log.error("  Instancia no existe: %s", instancia_path)
                todo_ok = False
                continue
            instancia = cargar_instancia(instancia_path, capacidad=cfg.capacidad)
            dist = calcular_matriz_distancias(instancia.nodos)
            res = algoritmo_memetico(instancia.nodos, cfg, dist=dist)
            costo_orig = data["costo_final"]
            ok = abs(res.costo_final - costo_orig) < tolerancia
            todo_ok = todo_ok and ok
            estado = "OK" if ok else "FALLO"
            log.info("  %s seed=%d costo_orig=%.6f costo_repro=%.6f", estado, cfg.seed, costo_orig, res.costo_final)
            detalles.append({
                "experimento": exp_dir.name,
                "seed": cfg.seed,
                "costo_original": costo_orig,
                "costo_reproducido": res.costo_final,
                "ok": ok,
            })
    return todo_ok, detalles


def _escribir_manifest(instancias: list[dict], runs: list[dict]) -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    manifest = {
        "git_commit_hash": git_commit_hash(),
        "versiones": versiones_runtime(),
        "instancias_versionadas": instancias,
        "runs_verificados": runs,
    }
    out = RESULTS / "MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log.info("Manifest escrito en %s", out.relative_to(ROOT))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica reproducibilidad del pipeline.")
    parser.add_argument(
        "--seeds-por-exp",
        type=int,
        default=1,
        help="Cuántos runs reproducir por experimento (default 1, modo smoke).",
    )
    parser.add_argument(
        "--tolerancia",
        type=float,
        default=1e-6,
        help="Tolerancia absoluta al comparar costos float.",
    )
    parser.add_argument(
        "--no-manifest",
        action="store_true",
        help="No escribir el MANIFEST.json al final.",
    )
    args = parser.parse_args()

    log.info("=== Verificando instancias ===")
    ok_inst, det_inst = _verificar_instancias()

    log.info("\n=== Verificando runs (modo smoke: %d seeds/exp) ===", args.seeds_por_exp)
    ok_runs, det_runs = _verificar_runs(args.seeds_por_exp, args.tolerancia)

    if not args.no_manifest:
        _escribir_manifest(det_inst, det_runs)

    if ok_inst and ok_runs:
        log.info("\n✓ Reproducibilidad verificada.")
        return 0
    log.error("\n✗ Reproducibilidad COMPROMETIDA.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
