"""Pruebas de Búsqueda Tabú: vecindad, memoria, aspiración y optimización."""

from __future__ import annotations

import numpy as np
import pytest

from memetico_cvrp.data import Nodo
from memetico_cvrp.distance import calcular_matriz_distancias
from memetico_cvrp.split import evaluar_cromosoma
from memetico_cvrp.tabu import (
    aplicar_aspiracion,
    es_tabu,
    generar_vecino_swap,
    optimizacion_tabu,
)


# ----------------------------- Vecino swap ------------------------------------


def test_swap_intercambia_genes() -> None:
    cromosoma = [1, 2, 3, 4, 5]
    vecino = generar_vecino_swap(cromosoma, 0, 4)
    assert vecino == [5, 2, 3, 4, 1]


def test_swap_es_funcion_pura() -> None:
    cromosoma = [1, 2, 3]
    vecino = generar_vecino_swap(cromosoma, 0, 2)
    assert cromosoma == [1, 2, 3]  # input intacto
    assert vecino == [3, 2, 1]


def test_swap_indices_iguales_levanta_error() -> None:
    with pytest.raises(ValueError, match="distintos"):
        generar_vecino_swap([1, 2, 3], 1, 1)


def test_swap_indice_fuera_de_rango_levanta_error() -> None:
    with pytest.raises(IndexError):
        generar_vecino_swap([1, 2, 3], 0, 5)


# ----------------------------- Memoria tabú -----------------------------------


def test_es_tabu_devuelve_true_si_no_expira() -> None:
    lista = {(1, 2): 10}
    assert es_tabu((1, 2), iteracion_actual=5, lista_tabu=lista) is True


def test_es_tabu_devuelve_false_si_ya_expiro() -> None:
    lista = {(1, 2): 5}
    assert es_tabu((1, 2), iteracion_actual=10, lista_tabu=lista) is False


def test_es_tabu_devuelve_false_si_no_existe() -> None:
    assert es_tabu((1, 2), iteracion_actual=0, lista_tabu={}) is False


def test_aspiracion_permite_mejorar_global() -> None:
    assert aplicar_aspiracion(costo_vecino=10.0, costo_mejor_global=15.0) is True
    assert aplicar_aspiracion(costo_vecino=20.0, costo_mejor_global=15.0) is False


# ----------------------------- Optimización -----------------------------------


def _instancia_simple(n: int = 10, seed: int = 42) -> tuple[dict[int, Nodo], np.ndarray, int]:
    """Construye una instancia chica reproducible para tests de Tabú."""
    rng = np.random.default_rng(seed)
    nodos: dict[int, Nodo] = {0: Nodo(id=0, x=50.0, y=50.0, demanda=0)}
    for i in range(1, n + 1):
        nodos[i] = Nodo(
            id=i,
            x=float(rng.integers(10, 91)),
            y=float(rng.integers(10, 91)),
            demanda=int(rng.integers(5, 16)),
        )
    dist = calcular_matriz_distancias(nodos)
    return nodos, dist, 50  # capacidad 50


def test_tabu_no_empeora_mejor_global() -> None:
    """El mejor global encontrado nunca puede ser peor que el inicial."""
    nodos, dist, cap = _instancia_simple(n=10)
    cromo_ini = list(range(1, 11))
    rng = np.random.default_rng(123)
    mejor, met = optimizacion_tabu(
        cromo_ini, dist, nodos, cap, rng=rng, iteraciones=30, tenencia=5, sample_size=20
    )
    assert met.costo_final <= met.costo_inicial


def test_tabu_resultado_es_factible() -> None:
    nodos, dist, cap = _instancia_simple(n=15)
    cromo_ini = list(range(1, 16))
    rng = np.random.default_rng(7)
    mejor, _ = optimizacion_tabu(
        cromo_ini, dist, nodos, cap, rng=rng, iteraciones=20, tenencia=5, sample_size=15
    )
    # Debe poder evaluarse sin levantar excepción y con permutación válida.
    res = evaluar_cromosoma(mejor, dist, nodos, cap)
    assert sorted(mejor) == list(range(1, 16))
    assert res.costo > 0


def test_tabu_misma_seed_mismo_resultado() -> None:
    nodos, dist, cap = _instancia_simple(n=12)
    cromo_ini = list(range(1, 13))
    a, _ = optimizacion_tabu(
        cromo_ini, dist, nodos, cap,
        rng=np.random.default_rng(99),
        iteraciones=25, tenencia=5, sample_size=15,
    )
    b, _ = optimizacion_tabu(
        cromo_ini, dist, nodos, cap,
        rng=np.random.default_rng(99),
        iteraciones=25, tenencia=5, sample_size=15,
    )
    assert a == b


def test_tabu_metricas_consistentes() -> None:
    nodos, dist, cap = _instancia_simple(n=10)
    cromo_ini = list(range(1, 11))
    rng = np.random.default_rng(0)
    _, met = optimizacion_tabu(
        cromo_ini, dist, nodos, cap, rng=rng, iteraciones=25, tenencia=5, sample_size=10
    )
    assert met.iteraciones == 25
    assert met.costo_inicial >= met.costo_final
    assert len(met.historico) == 26  # estado inicial + 25 iteraciones
    # El histórico debe ser monótonamente no creciente (es el mejor global).
    for i in range(1, len(met.historico)):
        assert met.historico[i] <= met.historico[i - 1]


def test_tabu_devuelve_intacto_si_n_menor_2() -> None:
    nodos = {0: Nodo(id=0, x=0.0, y=0.0, demanda=0), 1: Nodo(id=1, x=10.0, y=0.0, demanda=5)}
    dist = calcular_matriz_distancias(nodos)
    rng = np.random.default_rng(0)
    mejor, met = optimizacion_tabu(
        [1], dist, nodos, capacidad=10, rng=rng, iteraciones=5, tenencia=2, sample_size=3
    )
    assert mejor == [1]
    assert met.iteraciones == 0
