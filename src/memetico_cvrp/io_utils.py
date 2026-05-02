"""Persistencia, hashes y reproducibilidad de runs experimentales.

Cada run se serializa con metadatos completos (commit hash, versiones de
librerías, hash MD5 de la instancia, timestamp UTC) para que cualquier
resultado pueda ser auditado y reproducido bit-a-bit.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from memetico_cvrp.data import cargar_instancia
from memetico_cvrp.distance import calcular_matriz_distancias
from memetico_cvrp.memetic import ConfigMemetico, ResultadoMemetico, algoritmo_memetico


def hash_md5(path: str | Path) -> str:
    """MD5 hexadecimal de un archivo."""
    h = hashlib.md5()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit_hash() -> str:
    """Devuelve el hash corto del commit actual, o 'desconocido' si no hay git."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
        )
        return out.decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "desconocido"


def versiones_runtime() -> dict[str, str]:
    """Versiones de Python y libs científicas relevantes para reproducir."""
    info: dict[str, str] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
    }
    for libname in ("numpy", "pandas", "scipy", "matplotlib"):
        try:
            mod = __import__(libname)
            info[libname] = getattr(mod, "__version__", "desconocida")
        except ImportError:
            info[libname] = "no instalada"
    return info


def serializar_resultado(resultado: ResultadoMemetico) -> dict[str, Any]:
    """Convierte un ResultadoMemetico en un dict JSON-serializable."""
    return {
        "mejor_cromosoma": list(resultado.mejor_cromosoma),
        "costo_final": float(resultado.costo_final),
        "rutas": [list(r) for r in resultado.rutas],
        "cargas": [int(c) for c in resultado.cargas],
        "num_vehiculos": len(resultado.rutas),
        "historico_convergencia": [float(c) for c in resultado.historico_convergencia],
        "historico_promedio": [float(c) for c in resultado.historico_promedio],
        "tiempo_ejecucion": float(resultado.tiempo_ejecucion),
        "generacion_mejor": int(resultado.generacion_mejor),
        "iteraciones_tabu_aplicadas": int(resultado.iteraciones_tabu_aplicadas),
        "aceptaciones_no_mejorantes_tabu": int(resultado.aceptaciones_no_mejorantes_tabu),
        "configuracion": asdict(resultado.configuracion),
        "instancia_path": resultado.instancia_path,
        "instancia_hash": resultado.instancia_hash,
        "metricas_extra": dict(resultado.metricas_extra),
    }


def dump_run(
    resultado: ResultadoMemetico,
    output_dir: str | Path,
    seed: int,
    instancia_path: str | Path,
) -> Path:
    """Persiste un run individual en `<output_dir>/run_seed<seed>.json` con metadata.

    También exporta el histórico de convergencia en un CSV separado para gráficas.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = serializar_resultado(resultado)
    payload["meta"] = {
        "seed": seed,
        "git_commit_hash": git_commit_hash(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "instancia_path": str(instancia_path),
        "instancia_hash": hash_md5(instancia_path),
        "versiones": versiones_runtime(),
    }
    payload["instancia_path"] = str(instancia_path)
    payload["instancia_hash"] = payload["meta"]["instancia_hash"]

    json_path = output_dir / f"run_seed{seed}.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Histórico CSV para gráficas (gen, mejor_global, mejor_promedio).
    csv_path = output_dir / f"convergencia_seed{seed}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["generacion", "mejor_global", "promedio_poblacion"])
        for i, (mejor, prom) in enumerate(
            zip(resultado.historico_convergencia, resultado.historico_promedio)
        ):
            writer.writerow([i, f"{mejor:.6f}", f"{prom:.6f}"])

    return json_path


def cargar_run(path: str | Path) -> dict[str, Any]:
    """Carga un run JSON serializado."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def reproducir_run(run_path: str | Path) -> ResultadoMemetico:
    """Re-ejecuta un run a partir de su JSON serializado.

    Usa la misma instancia, capacidad, hiperparámetros y semilla. El resultado
    debe coincidir bit-a-bit con el original (mismo `costo_final`, mismo
    `mejor_cromosoma`).

    Raises
    ------
    ValueError
        Si el hash MD5 de la instancia ya no coincide (la instancia cambió).
    """
    data = cargar_run(run_path)
    meta = data["meta"]
    instancia_path = Path(meta["instancia_path"])
    if not instancia_path.is_absolute():
        # Resolver relativo al cwd del run (común: raíz del repo).
        instancia_path = Path.cwd() / instancia_path
    if not instancia_path.exists():
        # Reintentar relativo al directorio del JSON.
        instancia_path = Path(run_path).resolve().parent.parent.parent / meta["instancia_path"]

    hash_actual = hash_md5(instancia_path)
    if hash_actual != meta["instancia_hash"]:
        raise ValueError(
            f"La instancia {instancia_path} cambió desde el run original "
            f"(hash {hash_actual} vs {meta['instancia_hash']}). No se puede reproducir."
        )

    instancia = cargar_instancia(instancia_path)
    cfg_dict = data["configuracion"]
    config = ConfigMemetico(**cfg_dict)

    dist = calcular_matriz_distancias(instancia.nodos)
    return algoritmo_memetico(instancia.nodos, config, dist=dist)


def calcular_agregado(
    runs: list[dict[str, Any]],
    instancia_path: str | Path,
    capacidad: int,
) -> dict[str, Any]:
    """Resume estadísticamente un conjunto de runs del mismo experimento."""
    if not runs:
        return {}
    costos = [r["costo_final"] for r in runs]
    vehiculos = [r["num_vehiculos"] for r in runs]
    tiempos = [r["tiempo_ejecucion"] for r in runs]
    iter_tabu = [r["iteraciones_tabu_aplicadas"] for r in runs]
    no_mejorantes = [r["aceptaciones_no_mejorantes_tabu"] for r in runs]
    gen_mejor = [r["generacion_mejor"] for r in runs]

    # Demanda total (constante por instancia).
    instancia = cargar_instancia(instancia_path)
    demanda_total = sum(n.demanda for n in instancia.nodos.values())

    cargas_totales_por_run = [sum(r["cargas"]) for r in runs]
    capacidad_total_por_run = [capacidad * v for v in vehiculos]
    utilizaciones = [
        100.0 * c / k if k else 0.0 for c, k in zip(cargas_totales_por_run, capacidad_total_por_run)
    ]

    import statistics

    def _resumen(xs: list[float]) -> dict[str, float]:
        if not xs:
            return {}
        return {
            "min": float(min(xs)),
            "max": float(max(xs)),
            "media": float(statistics.fmean(xs)),
            "mediana": float(statistics.median(xs)),
            "std": float(statistics.pstdev(xs)) if len(xs) > 1 else 0.0,
        }

    return {
        "n_runs": len(runs),
        "seeds": [r["meta"]["seed"] for r in runs],
        "costo": _resumen(costos),
        "vehiculos": _resumen(vehiculos),
        "vehiculos_distribucion": vehiculos,
        "tiempo_segundos": _resumen(tiempos),
        "generacion_mejor": _resumen(gen_mejor),
        "iteraciones_tabu_total": sum(iter_tabu),
        "aceptaciones_no_mejorantes_tabu_total": sum(no_mejorantes),
        "utilizacion_promedio_pct": float(statistics.fmean(utilizaciones)),
        "utilizacion_distribucion_pct": utilizaciones,
        "demanda_total_instancia": demanda_total,
    }
