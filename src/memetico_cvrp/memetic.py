"""Orquestador del Algoritmo Memético: GA + Búsqueda Tabú + elitismo.

Flujo por generación:
1. Elitismo — el mejor cromosoma de la generación previa pasa intacto.
2. Mientras la nueva población no esté llena:
   a. Selección por torneo de dos padres.
   b. Cruza OX → hijo.
   c. Con probabilidad `prob_tabu`, el hijo se "educa" con Tabú.
3. Reemplazo total y registro del mejor global.

Cachéo de fitness: las evaluaciones son `O(N)` pero se invocan millones de
veces. Mantenemos un cache `tuple(cromosoma) -> costo` para evitar recomputar
fitness de individuos idénticos (típico cuando elitismo arrastra al campeón).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterable
from dataclasses import dataclass, field

import numpy as np

from memetico_cvrp.data import Nodo
from memetico_cvrp.distance import calcular_matriz_distancias
from memetico_cvrp.genetic import (
    crear_poblacion_inicial,
    cruza_ox,
    seleccion_torneo,
)
from memetico_cvrp.split import ResultadoSplit, evaluar_cromosoma
from memetico_cvrp.tabu import optimizacion_tabu

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConfigMemetico:
    """Hiperparámetros del Algoritmo Memético."""

    generaciones: int = 100
    tamano_poblacion: int = 60
    torneo_k: int = 3
    prob_tabu: float = 0.35
    iter_tabu: int = 30
    tenencia: int = 7
    sample_size: int = 25
    seed: int = 2026
    capacidad: int = 50
    mutacion_prob: float = 0.0  # opcional, default desactivada (Tabú actúa como super-mutación)

    def validar(self) -> None:
        if self.generaciones < 1:
            raise ValueError("generaciones debe ser >= 1")
        if self.tamano_poblacion < 2:
            raise ValueError("tamano_poblacion debe ser >= 2")
        if not 0.0 <= self.prob_tabu <= 1.0:
            raise ValueError("prob_tabu debe estar en [0, 1]")
        if not 0.0 <= self.mutacion_prob <= 1.0:
            raise ValueError("mutacion_prob debe estar en [0, 1]")


@dataclass
class ResultadoMemetico:
    """Resultado de una corrida completa del memético."""

    mejor_cromosoma: list[int]
    costo_final: float
    rutas: list[list[int]]
    cargas: list[int]
    historico_convergencia: list[float]
    historico_promedio: list[float]
    configuracion: ConfigMemetico
    tiempo_ejecucion: float
    generacion_mejor: int
    iteraciones_tabu_aplicadas: int
    aceptaciones_no_mejorantes_tabu: int
    instancia_path: str = ""
    instancia_hash: str = ""
    metricas_extra: dict = field(default_factory=dict)


def _diversidad(poblacion: Iterable[list[int]]) -> float:
    """Fracción de individuos únicos en la población (entre 0 y 1)."""
    pob_lista = list(poblacion)
    if not pob_lista:
        return 0.0
    unicos = {tuple(ind) for ind in pob_lista}
    return len(unicos) / len(pob_lista)


def algoritmo_memetico(
    nodos: dict[int, Nodo],
    config: ConfigMemetico,
    *,
    dist: np.ndarray | None = None,
) -> ResultadoMemetico:
    """Ejecuta el Algoritmo Memético sobre una instancia CVRP.

    Parameters
    ----------
    nodos
        Diccionario `{id: Nodo}` con el depósito en 0.
    config
        Hiperparámetros (`ConfigMemetico`).
    dist
        Matriz de distancias precalculada. Si es `None`, se calcula aquí.

    Returns
    -------
    ResultadoMemetico
        Mejor solución encontrada con histórico de convergencia y métricas.
    """
    config.validar()
    rng = np.random.default_rng(config.seed)
    if dist is None:
        dist = calcular_matriz_distancias(nodos)

    num_clientes = len(nodos) - 1
    cache_fitness: dict[tuple[int, ...], float] = {}

    def evaluar(cromo: list[int]) -> float:
        clave = tuple(cromo)
        if clave in cache_fitness:
            return cache_fitness[clave]
        costo = evaluar_cromosoma(cromo, dist, nodos, config.capacidad).costo
        cache_fitness[clave] = costo
        return costo

    poblacion = crear_poblacion_inicial(num_clientes, config.tamano_poblacion, rng=rng)
    fitness = [evaluar(ind) for ind in poblacion]

    mejor_global = list(poblacion[int(np.argmin(fitness))])
    costo_mejor_global = float(min(fitness))
    historico_convergencia = [costo_mejor_global]
    historico_promedio = [float(np.mean(fitness))]
    generacion_mejor = 0
    iteraciones_tabu = 0
    aceptaciones_no_mejorantes_tabu = 0

    log.info(
        "Inicio memético: N=%d gen=%d pob=%d seed=%d Q=%d | mejor inicial = %.2f",
        num_clientes,
        config.generaciones,
        config.tamano_poblacion,
        config.seed,
        config.capacidad,
        costo_mejor_global,
    )
    inicio = time.perf_counter()

    for gen in range(1, config.generaciones + 1):
        # Elitismo: el mejor de la generación previa pasa intacto a la siguiente.
        idx_mejor = int(np.argmin(fitness))
        nueva_poblacion: list[list[int]] = [list(poblacion[idx_mejor])]
        nuevo_fitness: list[float] = [fitness[idx_mejor]]

        while len(nueva_poblacion) < config.tamano_poblacion:
            padre1 = seleccion_torneo(poblacion, fitness, rng=rng, k=config.torneo_k)
            padre2 = seleccion_torneo(poblacion, fitness, rng=rng, k=config.torneo_k)
            hijo = cruza_ox(padre1, padre2, rng=rng)

            if config.mutacion_prob > 0.0 and rng.random() < config.mutacion_prob:
                # Mutación por swap aleatorio (rara, sólo si se activa explícitamente).
                i, j = rng.choice(len(hijo), size=2, replace=False).tolist()
                hijo[i], hijo[j] = hijo[j], hijo[i]

            if rng.random() < config.prob_tabu:
                hijo, met_tabu = optimizacion_tabu(
                    hijo,
                    dist,
                    nodos,
                    config.capacidad,
                    rng=rng,
                    iteraciones=config.iter_tabu,
                    tenencia=config.tenencia,
                    sample_size=config.sample_size,
                )
                iteraciones_tabu += met_tabu.iteraciones
                aceptaciones_no_mejorantes_tabu += met_tabu.aceptaciones_no_mejorantes
                if log.isEnabledFor(logging.DEBUG) and met_tabu.delta > 0:
                    log.debug(
                        "  Tabú gen %d: %.2f → %.2f (Δ=%.2f, mejoras=%d)",
                        gen,
                        met_tabu.costo_inicial,
                        met_tabu.costo_final,
                        met_tabu.delta,
                        met_tabu.mejoras,
                    )

            nueva_poblacion.append(hijo)
            nuevo_fitness.append(evaluar(hijo))

        poblacion = nueva_poblacion
        fitness = nuevo_fitness

        mejor_gen = float(min(fitness))
        if mejor_gen < costo_mejor_global:
            costo_mejor_global = mejor_gen
            mejor_global = list(poblacion[int(np.argmin(fitness))])
            generacion_mejor = gen
        historico_convergencia.append(costo_mejor_global)
        historico_promedio.append(float(np.mean(fitness)))

        log.info(
            "Gen %3d/%d | mejor_gen=%8.2f | mejor_global=%8.2f | diversidad=%.2f",
            gen,
            config.generaciones,
            mejor_gen,
            costo_mejor_global,
            _diversidad(poblacion),
        )

    duracion = time.perf_counter() - inicio
    res_split = evaluar_cromosoma(mejor_global, dist, nodos, config.capacidad)

    log.info(
        "Memético terminado en %.2fs | mejor=%.2f | vehículos=%d | gen_mejor=%d | iter_tabu=%d",
        duracion,
        costo_mejor_global,
        res_split.num_vehiculos,
        generacion_mejor,
        iteraciones_tabu,
    )

    return ResultadoMemetico(
        mejor_cromosoma=mejor_global,
        costo_final=costo_mejor_global,
        rutas=res_split.rutas,
        cargas=res_split.cargas,
        historico_convergencia=historico_convergencia,
        historico_promedio=historico_promedio,
        configuracion=config,
        tiempo_ejecucion=duracion,
        generacion_mejor=generacion_mejor,
        iteraciones_tabu_aplicadas=iteraciones_tabu,
        aceptaciones_no_mejorantes_tabu=aceptaciones_no_mejorantes_tabu,
    )


def evaluar_solucion_final(
    cromosoma: list[int],
    nodos: dict[int, Nodo],
    capacidad: int,
    dist: np.ndarray | None = None,
) -> ResultadoSplit:
    """Atajo: decodifica un cromosoma final usando una matriz de distancias compartida."""
    if dist is None:
        dist = calcular_matriz_distancias(nodos)
    return evaluar_cromosoma(cromosoma, dist, nodos, capacidad)
