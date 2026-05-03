"""Runner del playground Pyodide.

Pyodide carga este archivo y luego JavaScript llama a las funciones expuestas.
Hay dos modos:

1. **Bloqueante** — `correr_playground(...)` corre todo el algoritmo y devuelve
   el JSON final. Bloquea el JS event loop hasta terminar.

2. **Iterativo (paso a paso)** — `iniciar_run(...)`, `paso()`, `finalizar()`.
   JavaScript invoca `paso()` en un bucle cediendo control al event loop entre
   iteraciones (`await setTimeout(0)`); así la UI se actualiza en vivo.

Estado global: una sola corrida activa a la vez (`_estado`). Es razonable
porque cada navegador sirve a un único usuario.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any

if "/playground" not in sys.path:
    sys.path.insert(0, "/playground")

import numpy as np

from memetico_cvrp.data import cargar_instancia
from memetico_cvrp.distance import calcular_matriz_distancias
from memetico_cvrp.feasibility import validar_solucion
from memetico_cvrp.genetic import crear_poblacion_inicial, cruza_ox, seleccion_torneo
from memetico_cvrp.memetic import ConfigMemetico, _diversidad, algoritmo_memetico
from memetico_cvrp.split import evaluar_cromosoma
from memetico_cvrp.tabu import optimizacion_tabu


_estado: dict[str, Any] | None = None


def _serializar_resultado(estado: dict[str, Any], duracion: float) -> dict[str, Any]:
    """Construye el payload final con rutas, cargas, validación y nodos."""
    config: ConfigMemetico = estado["config"]
    instancia = estado["instancia"]
    dist = estado["dist"]
    mejor_global = estado["mejor_global"]
    res_split = evaluar_cromosoma(mejor_global, dist, instancia.nodos, config.capacidad)
    val = validar_solucion(
        res_split.rutas,
        instancia.nodos,
        config.capacidad,
        distancia_reportada=res_split.costo,
        dist_matriz=dist,
    )
    return {
        "ok": True,
        "tiempo_segundos": duracion,
        "costo_final": float(estado["costo_mejor_global"]),
        "num_vehiculos": len(res_split.rutas),
        "utilizacion_pct": val.utilizacion_pct,
        "generacion_mejor": estado["generacion_mejor"],
        "iteraciones_tabu_aplicadas": estado["iteraciones_tabu"],
        "aceptaciones_no_mejorantes_tabu": estado["aceptaciones_no_mejorantes_tabu"],
        "historico_convergencia": [float(c) for c in estado["historico_convergencia"]],
        "historico_promedio": [float(c) for c in estado["historico_promedio"]],
        "rutas": [[int(c) for c in r] for r in res_split.rutas],
        "cargas": [int(c) for c in res_split.cargas],
        "mejor_cromosoma": [int(c) for c in mejor_global],
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


# =================== MODO BLOQUEANTE (compat) =====================================


def correr_playground(
    seed: int = 2026,
    generaciones: int = 50,
    tamano_poblacion: int = 40,
    torneo_k: int = 3,
    prob_tabu: float = 0.30,
    iter_tabu: int = 20,
    tenencia: int = 5,
    sample_size: int = 15,
) -> str:
    """Corre el algoritmo memético completo y devuelve el JSON final."""
    instancia = cargar_instancia("/playground/instancia_base_25_q50.csv", capacidad=50)
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
    t0 = time.perf_counter()
    resultado = algoritmo_memetico(instancia.nodos, config, dist=dist)
    duracion = time.perf_counter() - t0

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


# =================== MODO ITERATIVO (paso a paso para UI en vivo) =================


def iniciar_run(
    seed: int = 2026,
    generaciones: int = 50,
    tamano_poblacion: int = 40,
    torneo_k: int = 3,
    prob_tabu: float = 0.30,
    iter_tabu: int = 20,
    tenencia: int = 5,
    sample_size: int = 15,
) -> str:
    """Inicializa una corrida iterativa. Devuelve un JSON con el estado inicial."""
    global _estado
    instancia = cargar_instancia("/playground/instancia_base_25_q50.csv", capacidad=50)
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
    config.validar()
    rng = np.random.default_rng(config.seed)
    num_clientes = len(instancia.nodos) - 1

    poblacion = crear_poblacion_inicial(num_clientes, config.tamano_poblacion, rng=rng)
    cache_fitness: dict[tuple[int, ...], float] = {}

    def evaluar(cromo: list[int]) -> float:
        clave = tuple(cromo)
        if clave in cache_fitness:
            return cache_fitness[clave]
        costo = evaluar_cromosoma(cromo, dist, instancia.nodos, config.capacidad).costo
        cache_fitness[clave] = costo
        return costo

    fitness = [evaluar(ind) for ind in poblacion]
    mejor_global = list(poblacion[int(np.argmin(fitness))])
    costo_mejor_global = float(min(fitness))

    _estado = {
        "config": config,
        "instancia": instancia,
        "dist": dist,
        "rng": rng,
        "poblacion": poblacion,
        "fitness": fitness,
        "mejor_global": mejor_global,
        "costo_mejor_global": costo_mejor_global,
        "generacion_mejor": 0,
        "historico_convergencia": [costo_mejor_global],
        "historico_promedio": [float(np.mean(fitness))],
        "iteraciones_tabu": 0,
        "aceptaciones_no_mejorantes_tabu": 0,
        "evaluar": evaluar,
        "gen_actual": 0,
        "t_inicio": time.perf_counter(),
    }
    return json.dumps(
        {
            "gen": 0,
            "total_gen": config.generaciones,
            "mejor_global": costo_mejor_global,
            "mejor_gen": costo_mejor_global,
            "promedio": float(np.mean(fitness)),
            "diversidad": _diversidad(poblacion),
            "mejor_cromosoma": list(mejor_global),
            "rutas_actuales": [
                [int(c) for c in r]
                for r in evaluar_cromosoma(
                    mejor_global, dist, instancia.nodos, config.capacidad
                ).rutas
            ],
        },
        ensure_ascii=False,
    )


def paso() -> str:
    """Avanza UNA generación del memético. Devuelve JSON con métricas + rutas actuales."""
    if _estado is None:
        raise RuntimeError("Llama iniciar_run() primero.")

    config: ConfigMemetico = _estado["config"]
    instancia = _estado["instancia"]
    dist = _estado["dist"]
    rng = _estado["rng"]
    poblacion = _estado["poblacion"]
    fitness = _estado["fitness"]
    evaluar = _estado["evaluar"]

    _estado["gen_actual"] += 1
    gen = _estado["gen_actual"]

    # Elitismo.
    idx_mejor = int(np.argmin(fitness))
    nueva_poblacion: list[list[int]] = [list(poblacion[idx_mejor])]
    nuevo_fitness: list[float] = [fitness[idx_mejor]]

    while len(nueva_poblacion) < config.tamano_poblacion:
        padre1 = seleccion_torneo(poblacion, fitness, rng=rng, k=config.torneo_k)
        padre2 = seleccion_torneo(poblacion, fitness, rng=rng, k=config.torneo_k)
        hijo = cruza_ox(padre1, padre2, rng=rng)

        if config.mutacion_prob > 0.0 and rng.random() < config.mutacion_prob:
            i, j = rng.choice(len(hijo), size=2, replace=False).tolist()
            hijo[i], hijo[j] = hijo[j], hijo[i]

        if rng.random() < config.prob_tabu:
            hijo, met_tabu = optimizacion_tabu(
                hijo,
                dist,
                instancia.nodos,
                config.capacidad,
                rng=rng,
                iteraciones=config.iter_tabu,
                tenencia=config.tenencia,
                sample_size=config.sample_size,
            )
            _estado["iteraciones_tabu"] += met_tabu.iteraciones
            _estado["aceptaciones_no_mejorantes_tabu"] += met_tabu.aceptaciones_no_mejorantes

        nueva_poblacion.append(hijo)
        nuevo_fitness.append(evaluar(hijo))

    _estado["poblacion"] = nueva_poblacion
    _estado["fitness"] = nuevo_fitness
    poblacion = nueva_poblacion
    fitness = nuevo_fitness

    mejor_gen = float(min(fitness))
    if mejor_gen < _estado["costo_mejor_global"]:
        _estado["costo_mejor_global"] = mejor_gen
        _estado["mejor_global"] = list(poblacion[int(np.argmin(fitness))])
        _estado["generacion_mejor"] = gen
    _estado["historico_convergencia"].append(_estado["costo_mejor_global"])
    _estado["historico_promedio"].append(float(np.mean(fitness)))

    rutas_actuales = evaluar_cromosoma(
        _estado["mejor_global"], dist, instancia.nodos, config.capacidad
    ).rutas

    return json.dumps(
        {
            "gen": gen,
            "total_gen": config.generaciones,
            "mejor_global": _estado["costo_mejor_global"],
            "mejor_gen": mejor_gen,
            "promedio": float(np.mean(fitness)),
            "diversidad": _diversidad(poblacion),
            "mejor_cromosoma": list(_estado["mejor_global"]),
            "rutas_actuales": [[int(c) for c in r] for r in rutas_actuales],
            "iteraciones_tabu_acumuladas": _estado["iteraciones_tabu"],
        },
        ensure_ascii=False,
    )


def finalizar() -> str:
    """Cierra la corrida iterativa y devuelve el JSON final completo."""
    if _estado is None:
        raise RuntimeError("Sin run activo.")
    duracion = time.perf_counter() - _estado["t_inicio"]
    payload = _serializar_resultado(_estado, duracion)
    return json.dumps(payload, ensure_ascii=False)


def reset() -> None:
    """Libera el estado en memoria (útil entre corridas largas)."""
    global _estado
    _estado = None
