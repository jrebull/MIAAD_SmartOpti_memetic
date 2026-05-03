"""Matriz de distancias euclidianas precalculada.

Calcular distancias en línea durante la evaluación de cromosomas es prohibitivo:
en un GA con 60 individuos × 100 generaciones × Tabú con 35 muestras × ~30 iteraciones
hablamos de millones de evaluaciones. Una matriz `(N+1) x (N+1)` precomputada
convierte cada distancia en un acceso O(1) a memoria.
"""

from __future__ import annotations

import numpy as np

from memetico_cvrp.data import Nodo


def calcular_matriz_distancias(nodos: dict[int, Nodo]) -> np.ndarray:
    """Devuelve la matriz simétrica `D[i, j]` con la distancia euclidiana entre nodos.

    Parameters
    ----------
    nodos
        Diccionario `{id: Nodo}` con IDs consecutivos 0..N (0 = depósito).

    Returns
    -------
    np.ndarray
        Matriz `float64` cuadrada de tamaño `(N+1, N+1)`, simétrica, con diagonal 0.

    Raises
    ------
    ValueError
        Si los IDs no son consecutivos desde 0.
    """
    n = len(nodos)
    ids = sorted(nodos.keys())
    if ids != list(range(n)):
        raise ValueError(f"IDs de nodos no son consecutivos desde 0: {ids[:5]}...")

    coords = np.empty((n, 2), dtype=np.float64)
    for nid in ids:
        coords[nid, 0] = nodos[nid].x
        coords[nid, 1] = nodos[nid].y

    # Broadcasting + np.hypot: estable numéricamente y vectorizado.
    diff_x = coords[:, 0:1] - coords[:, 0:1].T
    diff_y = coords[:, 1:2] - coords[:, 1:2].T
    dist = np.hypot(diff_x, diff_y)
    np.fill_diagonal(dist, 0.0)
    return dist
