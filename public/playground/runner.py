"""Runner del playground Pyodide.

Pyodide carga este archivo y luego JavaScript llama a `correr_playground(...)`.
Cada generación se reporta vía el callback que JS registra (proxy a una función
JS). Esto permite que la UI actualice convergencia, rutas y estado en vivo.

La instancia base (N=25, Q=50) se carga desde `/playground/instancia_base_25_q50.csv`.
El paquete `memetico_cvrp` se monta en `/playground/memetico_cvrp/` y se importa
con `sys.path.insert(0, "/playground")`.
"""

from __future__ import annotations

import io
import json
import sys
import time

# Asegurar que Pyodide pueda encontrar el paquete cargado al filesystem virtual.
if "/playground" not in sys.path:
    sys.path.insert(0, "/playground")

from memetico_cvrp.data import cargar_instancia
from memetico_cvrp.distance import calcular_matriz_distancias
from memetico_cvrp.feasibility import validar_solucion
from memetico_cvrp.memetic import ConfigMemetico, algoritmo_memetico


def correr_playground(
    seed: int = 2026,
    generaciones: int = 50,
    tamano_poblacion: int = 40,
    torneo_k: int = 3,
    prob_tabu: float = 0.30,
    iter_tabu: int = 20,
    tenencia: int = 5,
    sample_size: int = 15,
    on_generation=None,
) -> str:
    """Corre el algoritmo memético sobre la instancia base.

    `on_generation` es un proxy a una función JS que se invoca por generación.
    Devuelve un string JSON con el resultado final (más fácil de transferir
    a JavaScript que un dict Python rico).
    """
    instancia = cargar_instancia(
        "/playground/instancia_base_25_q50.csv",
        capacidad=50,
    )
    dist = calcular_matriz_distancias(instancia.nodos)

    config = ConfigMemetico(
        generaciones=int(generaciones),
        tamano_poblacion=int(tamano_poblacion),
        torneo_k=int(torneo_k),
        prob_tabu=float(prob_tabu),
        iter_tabu=int(iter_tabu),
        tenencia=int(tenencia),
        sample_size=int(sample_size),
        seed=int(seed),
        capacidad=instancia.capacidad,
    )

    def _cb(evento: dict) -> None:
        if on_generation is None:
            return
        # Convertir a JSON-string: Pyodide tiene fricción al pasar dicts a JS.
        on_generation(json.dumps(evento, ensure_ascii=False))

    t0 = time.perf_counter()
    resultado = algoritmo_memetico(
        instancia.nodos, config, dist=dist, on_generation=_cb,
    )
    duracion = time.perf_counter() - t0

    # Validación: nunca devolvemos algo infactible.
    val = validar_solucion(
        resultado.rutas,
        instancia.nodos,
        config.capacidad,
        distancia_reportada=resultado.costo_final,
        dist_matriz=dist,
    )

    payload = {
        "ok": True,
        "tiempo_segundos": duracion,
        "costo_final": float(resultado.costo_final),
        "num_vehiculos": len(resultado.rutas),
        "utilizacion_pct": val.utilizacion_pct,
        "generacion_mejor": resultado.generacion_mejor,
        "iteraciones_tabu_aplicadas": resultado.iteraciones_tabu_aplicadas,
        "aceptaciones_no_mejorantes_tabu": resultado.aceptaciones_no_mejorantes_tabu,
        "historico_convergencia": [float(c) for c in resultado.historico_convergencia],
        "historico_promedio": [float(c) for c in resultado.historico_promedio],
        "rutas": [[int(c) for c in r] for r in resultado.rutas],
        "cargas": [int(c) for c in resultado.cargas],
        "mejor_cromosoma": [int(c) for c in resultado.mejor_cromosoma],
        "configuracion": {
            "seed": config.seed,
            "generaciones": config.generaciones,
            "tamano_poblacion": config.tamano_poblacion,
            "torneo_k": config.torneo_k,
            "prob_tabu": config.prob_tabu,
            "iter_tabu": config.iter_tabu,
            "tenencia": config.tenencia,
            "sample_size": config.sample_size,
            "capacidad": config.capacidad,
        },
        "nodos": [
            {"id": n.id, "x": n.x, "y": n.y, "demanda": n.demanda}
            for n in instancia.nodos.values()
        ],
    }
    return json.dumps(payload, ensure_ascii=False)
