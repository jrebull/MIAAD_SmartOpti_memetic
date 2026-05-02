"""Pruebas del validador blindado de soluciones CVRP."""

from __future__ import annotations

import pytest

from memetico_cvrp.data import Nodo
from memetico_cvrp.distance import calcular_matriz_distancias
from memetico_cvrp.feasibility import SolucionInvalidaError, validar_solucion


def _nodos_demanda(demandas: list[int]) -> dict[int, Nodo]:
    nodos: dict[int, Nodo] = {0: Nodo(id=0, x=0.0, y=0.0, demanda=0)}
    for i, d in enumerate(demandas, start=1):
        nodos[i] = Nodo(id=i, x=float(i * 10), y=0.0, demanda=d)
    return nodos


def test_acepta_solucion_buena() -> None:
    nodos = _nodos_demanda([5, 5, 5])
    rutas = [[0, 1, 2, 3, 0]]
    res = validar_solucion(rutas, nodos, capacidad=20)
    assert res.factible is True
    assert res.num_vehiculos == 1
    assert res.cargas == [15]
    assert res.utilizacion_pct == pytest.approx(75.0)


def test_acepta_solucion_buena_con_distancia_reportada() -> None:
    nodos = _nodos_demanda([5, 5, 5])
    dist = calcular_matriz_distancias(nodos)
    rutas = [[0, 1, 2, 3, 0]]
    # Costo: 0→10→20→30→0 = 10+10+10+30 = 60
    res = validar_solucion(rutas, nodos, capacidad=20, distancia_reportada=60.0, dist_matriz=dist)
    assert res.factible is True
    assert res.costo_recalculado == pytest.approx(60.0)


def test_rechaza_cliente_duplicado() -> None:
    nodos = _nodos_demanda([5, 5, 5])
    rutas = [[0, 1, 2, 0], [0, 1, 3, 0]]  # cliente 1 duplicado
    with pytest.raises(SolucionInvalidaError, match="más de una vez"):
        validar_solucion(rutas, nodos, capacidad=20)


def test_rechaza_capacidad_excedida() -> None:
    nodos = _nodos_demanda([5, 5, 5])
    rutas = [[0, 1, 2, 3, 0]]
    with pytest.raises(SolucionInvalidaError, match="excede capacidad"):
        validar_solucion(rutas, nodos, capacidad=10)


def test_rechaza_cliente_faltante() -> None:
    nodos = _nodos_demanda([5, 5, 5])
    rutas = [[0, 1, 2, 0]]  # falta cliente 3
    with pytest.raises(SolucionInvalidaError, match="faltantes"):
        validar_solucion(rutas, nodos, capacidad=20)


def test_rechaza_distancia_falsa() -> None:
    nodos = _nodos_demanda([5, 5, 5])
    rutas = [[0, 1, 2, 3, 0]]
    with pytest.raises(SolucionInvalidaError, match="no coincide"):
        validar_solucion(rutas, nodos, capacidad=20, distancia_reportada=999.0)


def test_rechaza_ruta_que_no_inicia_en_deposito() -> None:
    nodos = _nodos_demanda([5, 5, 5])
    rutas = [[1, 2, 3, 0]]
    with pytest.raises(SolucionInvalidaError, match="depósito"):
        validar_solucion(rutas, nodos, capacidad=20)


def test_rechaza_ruta_vacia() -> None:
    nodos = _nodos_demanda([5])
    rutas: list[list[int]] = []
    with pytest.raises(SolucionInvalidaError, match="ninguna ruta"):
        validar_solucion(rutas, nodos, capacidad=10)


def test_rechaza_id_extra_en_solucion() -> None:
    nodos = _nodos_demanda([5, 5])
    rutas = [[0, 1, 2, 99, 0]]
    with pytest.raises(SolucionInvalidaError, match="rango"):
        validar_solucion(rutas, nodos, capacidad=20)


def test_utilizacion_correcta() -> None:
    """Demanda total 30, dos vehículos de 25 → utilización 30/50 = 60%."""
    nodos = _nodos_demanda([10, 10, 10])
    rutas = [[0, 1, 2, 0], [0, 3, 0]]
    res = validar_solucion(rutas, nodos, capacidad=25)
    assert res.utilizacion_pct == pytest.approx(60.0)
