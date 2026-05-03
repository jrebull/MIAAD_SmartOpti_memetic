"""Búsqueda Tabú con tenencia y criterio de aspiración para cromosomas CVRP.

Operador de vecindad: swap de dos clientes en el Giant Tour.
Memoria: lista tabú estática con tenencia `T`, indexada por el par normalizado
`(min(c_a, c_b), max(c_a, c_b))`.
Aspiración: aceptar un movimiento tabú si mejora el mejor global.
Muestreo: en cada iteración se exploran `sample_size` swaps aleatorios (no todos
los `O(N^2)`), elegidos por el `np.random.Generator` inyectado.

Esta es la "intensificación local" del Algoritmo Memético: educa cada hijo
prometedor antes de devolverlo a la siguiente generación.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from memetico_cvrp.data import Nodo
from memetico_cvrp.split import evaluar_cromosoma


@dataclass
class MetricasTabu:
    """Métricas devueltas por una corrida de Tabú (útiles para el reporte)."""

    costo_inicial: float
    costo_final: float
    mejoras: int
    aceptaciones_no_mejorantes: int
    historico: list[float]
    iteraciones: int

    @property
    def delta(self) -> float:
        return self.costo_inicial - self.costo_final


def generar_vecino_swap(cromosoma: list[int], i: int, j: int) -> list[int]:
    """Devuelve una copia del cromosoma con `i` y `j` intercambiados (función pura).

    Parameters
    ----------
    cromosoma
        Permutación de clientes.
    i, j
        Índices distintos en `[0, len(cromosoma))`.
    """
    n = len(cromosoma)
    if not (0 <= i < n and 0 <= j < n):
        raise IndexError(f"Índices fuera de rango ({i}, {j}) para longitud {n}")
    if i == j:
        raise ValueError("i y j deben ser distintos.")
    vecino = list(cromosoma)
    vecino[i], vecino[j] = vecino[j], vecino[i]
    return vecino


def es_tabu(
    movimiento: tuple[int, int],
    iteracion_actual: int,
    lista_tabu: dict[tuple[int, int], int],
) -> bool:
    """`True` si `movimiento` está prohibido en la `iteracion_actual`."""
    expira_en = lista_tabu.get(movimiento, 0)
    return expira_en > iteracion_actual


def aplicar_aspiracion(costo_vecino: float, costo_mejor_global: float) -> bool:
    """Criterio de aspiración estándar: el vecino mejora el mejor global."""
    return costo_vecino < costo_mejor_global


def optimizacion_tabu(
    cromosoma_inicial: list[int],
    dist: np.ndarray,
    nodos: dict[int, Nodo],
    capacidad: int,
    rng: np.random.Generator,
    *,
    iteraciones: int = 25,
    tenencia: int = 7,
    sample_size: int = 25,
) -> tuple[list[int], MetricasTabu]:
    """Optimiza un cromosoma con Búsqueda Tabú (swap + tenencia + aspiración).

    Política de aceptación: en cada iteración se muestrean `sample_size` swaps
    aleatorios; el mejor entre los aceptables (no-tabú o que cumple aspiración)
    se acepta como nuevo `actual`, **incluso si empeora**. Esto es lo que
    distingue Tabú del descenso glotón: permite escapar de óptimos locales.

    Parameters
    ----------
    cromosoma_inicial
        Punto de partida (típicamente un hijo recién cruzado por OX).
    dist
        Matriz de distancias precalculada.
    nodos, capacidad
        Para evaluar cada vecino vía `evaluar_cromosoma`.
    rng
        `np.random.Generator` inyectado.
    iteraciones
        Presupuesto de iteraciones (corto: 20-35 por hijo).
    tenencia
        Cuántas iteraciones permanece prohibido un movimiento aceptado.
    sample_size
        Vecinos muestreados por iteración (en lugar de los O(N^2) posibles).

    Returns
    -------
    tuple[list[int], MetricasTabu]
        Mejor cromosoma encontrado (nunca infactible) y métricas de la corrida.
    """
    n = len(cromosoma_inicial)
    if n < 2:
        # Sin margen para hacer swaps: devolvemos el cromosoma intacto.
        costo_ini = evaluar_cromosoma(cromosoma_inicial, dist, nodos, capacidad).costo
        return list(cromosoma_inicial), MetricasTabu(
            costo_inicial=costo_ini,
            costo_final=costo_ini,
            mejoras=0,
            aceptaciones_no_mejorantes=0,
            historico=[costo_ini],
            iteraciones=0,
        )

    actual = list(cromosoma_inicial)
    costo_actual = evaluar_cromosoma(actual, dist, nodos, capacidad).costo

    mejor_global = list(actual)
    costo_mejor_global = costo_actual
    historico = [costo_mejor_global]

    lista_tabu: dict[tuple[int, int], int] = {}
    mejoras = 0
    aceptaciones_no_mejorantes = 0
    sample_efectivo = max(1, min(sample_size, n * (n - 1) // 2))

    for it in range(iteraciones):
        mejor_vecino: list[int] | None = None
        mejor_costo = float("inf")
        mejor_movimiento: tuple[int, int] | None = None

        for _ in range(sample_efectivo):
            i, j = rng.choice(n, size=2, replace=False).tolist()
            vecino = generar_vecino_swap(actual, i, j)
            costo_v = evaluar_cromosoma(vecino, dist, nodos, capacidad).costo

            c_a = actual[i]
            c_b = actual[j]
            movimiento = (min(c_a, c_b), max(c_a, c_b))

            if es_tabu(movimiento, it, lista_tabu) and not aplicar_aspiracion(
                costo_v, costo_mejor_global
            ):
                continue
            if costo_v < mejor_costo:
                mejor_vecino = vecino
                mejor_costo = costo_v
                mejor_movimiento = movimiento

        if mejor_vecino is None:
            historico.append(costo_mejor_global)
            continue

        if mejor_costo >= costo_actual:
            aceptaciones_no_mejorantes += 1

        actual = mejor_vecino
        costo_actual = mejor_costo
        if mejor_movimiento is not None:
            lista_tabu[mejor_movimiento] = it + tenencia + 1

        if costo_actual < costo_mejor_global:
            mejor_global = list(actual)
            costo_mejor_global = costo_actual
            mejoras += 1

        historico.append(costo_mejor_global)

    metricas = MetricasTabu(
        costo_inicial=historico[0],
        costo_final=costo_mejor_global,
        mejoras=mejoras,
        aceptaciones_no_mejorantes=aceptaciones_no_mejorantes,
        historico=historico,
        iteraciones=iteraciones,
    )
    return mejor_global, metricas
