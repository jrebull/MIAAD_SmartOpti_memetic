"""Pruebas de la matriz de distancias euclidianas."""

from __future__ import annotations

import numpy as np
import pytest

from memetico_cvrp.data import Nodo
from memetico_cvrp.distance import calcular_matriz_distancias


def _nodos(coords: list[tuple[int, int]]) -> dict[int, Nodo]:
    """Helper: construye dict de nodos a partir de una lista de coordenadas."""
    return {
        i: Nodo(id=i, x=float(x), y=float(y), demanda=0 if i == 0 else 5)
        for i, (x, y) in enumerate(coords)
    }


def test_diagonal_cero() -> None:
    nodos = _nodos([(0, 0), (3, 4), (5, 12)])
    d = calcular_matriz_distancias(nodos)
    assert np.all(np.diag(d) == 0.0)


def test_simetria() -> None:
    nodos = _nodos([(0, 0), (3, 4), (5, 12), (8, 6)])
    d = calcular_matriz_distancias(nodos)
    assert np.allclose(d, d.T)


def test_distancia_conocida_3_4_5() -> None:
    """Triángulo 3-4-5: la hipotenusa entre (0,0) y (3,4) debe ser 5.0 exacto."""
    nodos = _nodos([(0, 0), (3, 4)])
    d = calcular_matriz_distancias(nodos)
    assert d[0, 1] == 5.0
    assert d[1, 0] == 5.0


def test_dimensiones_correctas() -> None:
    nodos = _nodos([(50, 50), (10, 20), (80, 90), (40, 60), (70, 30)])
    d = calcular_matriz_distancias(nodos)
    assert d.shape == (5, 5)
    assert d.dtype == np.float64


def test_rechaza_ids_no_consecutivos() -> None:
    nodos = {
        0: Nodo(id=0, x=50.0, y=50.0, demanda=0),
        2: Nodo(id=2, x=10.0, y=20.0, demanda=5),
    }
    with pytest.raises(ValueError, match="consecutivos"):
        calcular_matriz_distancias(nodos)


def test_distancias_no_negativas() -> None:
    nodos = _nodos([(0, 0), (10, 0), (0, 10), (10, 10)])
    d = calcular_matriz_distancias(nodos)
    assert np.all(d >= 0.0)
