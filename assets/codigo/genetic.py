"""Operadores genéticos para cromosomas tipo permutación (Giant Tour).

Implementaciones desde cero, sin librerías evolutivas externas:
- crear_poblacion_inicial: muestreo de permutaciones reproducible y diverso.
- seleccion_torneo: presión selectiva controlada por k, sin mutar la población.
- cruza_ox: Order Crossover preservando invariantes de permutación.

El generador de números aleatorios es siempre `np.random.Generator` inyectado
desde fuera (NO usamos el global de `random` ni `np.random`). Esto garantiza
reproducibilidad bit-a-bit con cualquier semilla.
"""

from __future__ import annotations

import numpy as np


def crear_poblacion_inicial(
    num_clientes: int,
    tamano_pob: int,
    rng: np.random.Generator,
    *,
    max_intentos_diversidad: int = 100,
) -> list[list[int]]:
    """Genera una población de permutaciones de `1..num_clientes`.

    Parameters
    ----------
    num_clientes
        Cantidad de clientes (cromosoma de longitud N).
    tamano_pob
        Tamaño exacto de la población a producir.
    rng
        Generador `np.random.Generator` inyectado (reproducible).
    max_intentos_diversidad
        Reintentos para evitar individuos duplicados antes de aceptarlos
        (relevante sólo cuando `tamano_pob` se acerca a `num_clientes!`).

    Returns
    -------
    list[list[int]]
        Población de tamaño `tamano_pob`, cada individuo permutación válida.
    """
    if num_clientes < 1:
        raise ValueError(f"num_clientes debe ser >= 1, recibido {num_clientes}")
    if tamano_pob < 1:
        raise ValueError(f"tamano_pob debe ser >= 1, recibido {tamano_pob}")

    base = np.arange(1, num_clientes + 1)
    poblacion: list[list[int]] = []
    vistos: set[tuple[int, ...]] = set()

    while len(poblacion) < tamano_pob:
        permu = rng.permutation(base).tolist()
        clave = tuple(permu)
        if clave in vistos:
            # Sólo intentamos rerandomizar si hay margen combinatorio razonable.
            intentos = 0
            while clave in vistos and intentos < max_intentos_diversidad:
                permu = rng.permutation(base).tolist()
                clave = tuple(permu)
                intentos += 1
        vistos.add(clave)
        poblacion.append(permu)

    return poblacion


def seleccion_torneo(
    poblacion: list[list[int]],
    fitness: list[float] | np.ndarray,
    rng: np.random.Generator,
    k: int = 3,
) -> list[int]:
    """Selección por torneo de tamaño `k` sobre `poblacion` (minimización).

    Devuelve **una copia** del cromosoma ganador para evitar aliasing en cruzas
    posteriores; nunca muta la población original.

    Parameters
    ----------
    poblacion, fitness
        Listas paralelas: `fitness[i]` corresponde a `poblacion[i]`.
    rng
        Generador `np.random.Generator` inyectado.
    k
        Tamaño del torneo (>= 1, default 3). Si `k >= len(poblacion)` se reduce.

    Returns
    -------
    list[int]
        Copia del cromosoma con menor fitness entre los `k` participantes.
    """
    n = len(poblacion)
    if n == 0:
        raise ValueError("Población vacía.")
    if len(fitness) != n:
        raise ValueError(f"len(fitness)={len(fitness)} != len(poblacion)={n}")
    k_efectivo = max(1, min(k, n))

    indices = rng.choice(n, size=k_efectivo, replace=False)
    fitness_arr = np.asarray(fitness, dtype=float)
    ganador = int(indices[int(np.argmin(fitness_arr[indices]))])
    return list(poblacion[ganador])


def cruza_ox(
    padre1: list[int],
    padre2: list[int],
    rng: np.random.Generator,
) -> list[int]:
    """Order Crossover (OX) entre dos permutaciones de igual longitud.

    Algoritmo (Davis, 1985):
    1. Se eligen dos puntos de corte `pto1 <= pto2` al azar.
    2. El segmento `[pto1:pto2+1]` del `padre1` se copia tal cual en el hijo.
    3. Los huecos restantes se rellenan recorriendo `padre2` desde la posición
       `pto2+1` (con wrap-around), saltándose los genes ya presentes en el hijo.

    Resultado: hijo es permutación válida con
    `set(hijo) == set(padre1) == set(padre2)` y conserva orden relativo de
    los genes "no copiados" del padre2.

    Parameters
    ----------
    padre1, padre2
        Cromosomas permutación de la misma longitud y mismo conjunto de genes.
    rng
        Generador `np.random.Generator` inyectado.

    Returns
    -------
    list[int]
        Hijo permutación válida.
    """
    n = len(padre1)
    if n != len(padre2):
        raise ValueError(f"Padres de longitud distinta: {n} vs {len(padre2)}")
    if set(padre1) != set(padre2):
        raise ValueError("Padres con conjuntos de genes distintos.")
    if n == 0:
        return []
    if n == 1:
        return list(padre1)

    pto1, pto2 = sorted(rng.choice(n, size=2, replace=False).tolist())

    hijo: list[int | None] = [None] * n
    segmento = padre1[pto1 : pto2 + 1]
    hijo[pto1 : pto2 + 1] = segmento

    en_hijo = set(segmento)
    pos_hijo = (pto2 + 1) % n
    pos_padre = (pto2 + 1) % n
    while None in hijo:
        gen = padre2[pos_padre]
        if gen not in en_hijo:
            hijo[pos_hijo] = gen
            en_hijo.add(gen)
            pos_hijo = (pos_hijo + 1) % n
        pos_padre = (pos_padre + 1) % n

    return [g for g in hijo if g is not None]
