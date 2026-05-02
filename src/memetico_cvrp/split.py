"""Decodificador Split capacitado: convierte un Giant Tour en rutas factibles.

Estrategia: recorre el cromosoma de izquierda a derecha y va llenando un vehículo
hasta que la siguiente demanda lo desbordaría; en ese punto cierra la ruta (regreso
al depósito 0) y abre una nueva. Es el algoritmo Split más simple — determinista,
O(N) y respeta el orden inducido por la permutación.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from memetico_cvrp.data import Nodo


@dataclass(frozen=True)
class ResultadoSplit:
    """Resultado de decodificar un cromosoma."""

    costo: float
    rutas: list[list[int]]
    cargas: list[int]

    @property
    def num_vehiculos(self) -> int:
        return len(self.rutas)


def evaluar_cromosoma(
    cromosoma: list[int],
    dist: np.ndarray,
    nodos: dict[int, Nodo],
    capacidad: int,
) -> ResultadoSplit:
    """Decodifica un Giant Tour en rutas factibles y calcula su costo total.

    Parameters
    ----------
    cromosoma
        Permutación de los IDs de cliente `1..N` (sin el depósito).
    dist
        Matriz de distancias precalculada `(N+1) x (N+1)`.
    nodos
        Diccionario `{id: Nodo}` con las demandas.
    capacidad
        Capacidad máxima `Q` de cada vehículo de la flota homogénea.

    Returns
    -------
    ResultadoSplit
        `costo` (distancia total euclidiana), `rutas` (cada ruta inicia y termina
        en 0), `cargas` (suma de demandas por ruta).

    Raises
    ------
    ValueError
        Si el cromosoma tiene clientes duplicados, faltantes, o si algún cliente
        individual tiene demanda mayor que la capacidad.
    """
    if not cromosoma:
        raise ValueError("Cromosoma vacío.")

    clientes_esperados = set(range(1, len(nodos)))
    cromosoma_set = set(cromosoma)

    if len(cromosoma) != len(cromosoma_set):
        duplicados = [c for c in cromosoma if cromosoma.count(c) > 1]
        raise ValueError(f"Cromosoma con clientes duplicados: {sorted(set(duplicados))[:10]}")

    faltantes = clientes_esperados - cromosoma_set
    if faltantes:
        raise ValueError(f"Cromosoma con clientes faltantes: {sorted(faltantes)[:10]}")

    extras = cromosoma_set - clientes_esperados
    if extras:
        raise ValueError(f"Cromosoma con IDs fuera del rango 1..N: {sorted(extras)[:10]}")

    for cid in cromosoma:
        if nodos[cid].demanda > capacidad:
            raise ValueError(
                f"Cliente {cid} tiene demanda {nodos[cid].demanda} > capacidad {capacidad}: "
                "instancia inviable."
            )

    rutas: list[list[int]] = []
    cargas: list[int] = []
    costo_total = 0.0

    ruta_actual: list[int] = [0]
    carga_actual = 0

    for cliente in cromosoma:
        demanda = nodos[cliente].demanda
        if carga_actual + demanda > capacidad:
            # Cerrar la ruta actual y abrir una nueva.
            ruta_actual.append(0)
            costo_total += _costo_ruta(ruta_actual, dist)
            rutas.append(ruta_actual)
            cargas.append(carga_actual)
            ruta_actual = [0, cliente]
            carga_actual = demanda
        else:
            ruta_actual.append(cliente)
            carga_actual += demanda

    # Cerrar la última ruta pendiente.
    if len(ruta_actual) > 1:
        ruta_actual.append(0)
        costo_total += _costo_ruta(ruta_actual, dist)
        rutas.append(ruta_actual)
        cargas.append(carga_actual)

    return ResultadoSplit(costo=costo_total, rutas=rutas, cargas=cargas)


def _costo_ruta(ruta: list[int], dist: np.ndarray) -> float:
    """Suma de distancias de los arcos de una ruta."""
    return float(sum(dist[ruta[i], ruta[i + 1]] for i in range(len(ruta) - 1)))
