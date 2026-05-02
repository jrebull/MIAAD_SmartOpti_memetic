"""Pruebas del decodificador Split capacitado."""

from __future__ import annotations

import pytest

from memetico_cvrp.data import Nodo
from memetico_cvrp.distance import calcular_matriz_distancias
from memetico_cvrp.split import evaluar_cromosoma


def _nodos_demanda(demandas: list[int]) -> dict[int, Nodo]:
    """Helper: construye nodos colineales con las demandas dadas (cliente i en x=i*10)."""
    nodos: dict[int, Nodo] = {0: Nodo(id=0, x=0.0, y=0.0, demanda=0)}
    for i, d in enumerate(demandas, start=1):
        nodos[i] = Nodo(id=i, x=float(i * 10), y=0.0, demanda=d)
    return nodos


def test_caso_simple_3_clientes_un_vehiculo() -> None:
    """3 clientes con demandas que caben juntas en un solo vehículo."""
    nodos = _nodos_demanda([5, 5, 5])
    dist = calcular_matriz_distancias(nodos)
    res = evaluar_cromosoma([1, 2, 3], dist, nodos, capacidad=20)
    assert res.num_vehiculos == 1
    assert res.rutas[0] == [0, 1, 2, 3, 0]
    assert res.cargas == [15]
    # Distancia: 0→10→20→30→0 = 10+10+10+30 = 60
    assert res.costo == pytest.approx(60.0)


def test_forzar_segundo_vehiculo() -> None:
    """Si la suma de demandas excede la capacidad, debe abrir una segunda ruta."""
    nodos = _nodos_demanda([6, 6, 6])
    dist = calcular_matriz_distancias(nodos)
    res = evaluar_cromosoma([1, 2, 3], dist, nodos, capacidad=10)
    # Capacidad 10: cliente 1 (carga=6), cliente 2 desbordaría → cierra ruta1 y abre ruta2.
    assert res.num_vehiculos == 3 or res.num_vehiculos == 2
    # Total demanda atendida = 18
    assert sum(res.cargas) == 18


def test_demanda_exacta_capacidad() -> None:
    """Si una demanda iguala la capacidad, ese cliente forma su propia ruta."""
    nodos = _nodos_demanda([10, 5, 5])
    dist = calcular_matriz_distancias(nodos)
    res = evaluar_cromosoma([1, 2, 3], dist, nodos, capacidad=10)
    # Cliente 1 llena por sí solo el vehículo (carga=10), después clientes 2 y 3 (carga=10).
    assert res.num_vehiculos == 2
    assert res.cargas == [10, 10]
    for ruta in res.rutas:
        assert ruta[0] == 0 and ruta[-1] == 0


def test_todas_las_rutas_inician_y_terminan_en_deposito() -> None:
    nodos = _nodos_demanda([5, 5, 5, 5, 5])
    dist = calcular_matriz_distancias(nodos)
    res = evaluar_cromosoma([3, 1, 5, 2, 4], dist, nodos, capacidad=12)
    for ruta in res.rutas:
        assert ruta[0] == 0
        assert ruta[-1] == 0


def test_cubre_todos_los_clientes_exactamente_una_vez() -> None:
    nodos = _nodos_demanda([4, 7, 3, 8, 2, 6])
    dist = calcular_matriz_distancias(nodos)
    res = evaluar_cromosoma([2, 5, 1, 6, 4, 3], dist, nodos, capacidad=15)
    visitados: list[int] = []
    for ruta in res.rutas:
        visitados.extend([c for c in ruta if c != 0])
    assert sorted(visitados) == [1, 2, 3, 4, 5, 6]


def test_cargas_no_exceden_capacidad() -> None:
    nodos = _nodos_demanda([4, 7, 3, 8, 2, 6, 9, 5])
    dist = calcular_matriz_distancias(nodos)
    res = evaluar_cromosoma([1, 2, 3, 4, 5, 6, 7, 8], dist, nodos, capacidad=15)
    for carga in res.cargas:
        assert carga <= 15


def test_costo_coincide_con_suma_de_aristas() -> None:
    nodos = _nodos_demanda([5, 5, 5])
    dist = calcular_matriz_distancias(nodos)
    res = evaluar_cromosoma([1, 2, 3], dist, nodos, capacidad=15)
    costo_recalc = 0.0
    for ruta in res.rutas:
        for i in range(len(ruta) - 1):
            costo_recalc += dist[ruta[i], ruta[i + 1]]
    assert res.costo == pytest.approx(costo_recalc)


def test_cromosoma_con_duplicados_levanta_error() -> None:
    nodos = _nodos_demanda([5, 5, 5])
    dist = calcular_matriz_distancias(nodos)
    with pytest.raises(ValueError, match="duplicados"):
        evaluar_cromosoma([1, 2, 2], dist, nodos, capacidad=15)


def test_cromosoma_con_faltantes_levanta_error() -> None:
    nodos = _nodos_demanda([5, 5, 5])
    dist = calcular_matriz_distancias(nodos)
    with pytest.raises(ValueError, match="faltantes"):
        evaluar_cromosoma([1, 2], dist, nodos, capacidad=15)


def test_cromosoma_vacio_levanta_error() -> None:
    nodos = _nodos_demanda([5])
    dist = calcular_matriz_distancias(nodos)
    with pytest.raises(ValueError, match="vacío"):
        evaluar_cromosoma([], dist, nodos, capacidad=10)


def test_cliente_demanda_mayor_que_capacidad_levanta_error() -> None:
    """Si un cliente individual no cabe en ningún vehículo, instancia inviable."""
    nodos = _nodos_demanda([5, 20, 5])
    dist = calcular_matriz_distancias(nodos)
    with pytest.raises(ValueError, match="capacidad"):
        evaluar_cromosoma([1, 2, 3], dist, nodos, capacidad=10)


def test_cromosoma_con_id_fuera_de_rango_levanta_error() -> None:
    """Cromosoma cubre todos los clientes esperados pero incluye un ID extra."""
    nodos = _nodos_demanda([5, 5, 5])
    dist = calcular_matriz_distancias(nodos)
    with pytest.raises(ValueError, match="rango"):
        evaluar_cromosoma([1, 2, 3, 99], dist, nodos, capacidad=15)


def test_un_solo_cliente() -> None:
    """Caso degenerado: 1 cliente, 1 vehículo, ruta 0→1→0."""
    nodos = _nodos_demanda([7])
    dist = calcular_matriz_distancias(nodos)
    res = evaluar_cromosoma([1], dist, nodos, capacidad=10)
    assert res.num_vehiculos == 1
    assert res.rutas[0] == [0, 1, 0]
    assert res.cargas == [7]
    assert res.costo == pytest.approx(20.0)  # 0→10→0
