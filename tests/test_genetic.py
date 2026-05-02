"""Pruebas de operadores genéticos: población, torneo y OX."""

from __future__ import annotations

import numpy as np
import pytest

from memetico_cvrp.genetic import (
    crear_poblacion_inicial,
    cruza_ox,
    seleccion_torneo,
)


# --------------------------- Población inicial --------------------------------


def test_poblacion_tamano_exacto() -> None:
    rng = np.random.default_rng(42)
    pob = crear_poblacion_inicial(num_clientes=10, tamano_pob=20, rng=rng)
    assert len(pob) == 20


@pytest.mark.parametrize("n", [5, 10, 25, 100])
def test_individuos_son_permutaciones_validas(n: int) -> None:
    rng = np.random.default_rng(123)
    pob = crear_poblacion_inicial(num_clientes=n, tamano_pob=15, rng=rng)
    for ind in pob:
        assert len(ind) == n
        assert sorted(ind) == list(range(1, n + 1))


def test_misma_seed_misma_poblacion() -> None:
    pob_a = crear_poblacion_inicial(20, 30, rng=np.random.default_rng(7))
    pob_b = crear_poblacion_inicial(20, 30, rng=np.random.default_rng(7))
    assert pob_a == pob_b


def test_diversidad_alta_para_n_grande() -> None:
    """Con 50 clientes y 30 individuos, todos deben ser distintos."""
    rng = np.random.default_rng(11)
    pob = crear_poblacion_inicial(50, 30, rng=rng)
    claves = {tuple(ind) for ind in pob}
    assert len(claves) == 30


def test_rechaza_num_clientes_invalido() -> None:
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError):
        crear_poblacion_inicial(0, 5, rng=rng)


def test_rechaza_tamano_pob_invalido() -> None:
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError):
        crear_poblacion_inicial(5, 0, rng=rng)


# --------------------------- Selección por torneo -----------------------------


def test_torneo_devuelve_mejor_de_k() -> None:
    """Con todos los fitness conocidos, el mejor del torneo debe tener el menor."""
    pob = [[1, 2, 3], [3, 2, 1], [2, 3, 1], [1, 3, 2]]
    fit = [10.0, 5.0, 7.0, 12.0]
    rng = np.random.default_rng(0)
    # Forzamos k = len(pob): el mejor (índice 1, fit 5.0) siempre gana.
    ganador = seleccion_torneo(pob, fit, rng=rng, k=len(pob))
    assert ganador == [3, 2, 1]


def test_torneo_no_muta_poblacion() -> None:
    pob = [[1, 2, 3], [3, 2, 1]]
    pob_copia = [list(ind) for ind in pob]
    fit = [10.0, 5.0]
    rng = np.random.default_rng(1)
    ganador = seleccion_torneo(pob, fit, rng=rng, k=2)
    assert pob == pob_copia
    # El ganador debe ser una copia, no el mismo objeto.
    ganador[0] = 999
    assert pob[1][0] == 3


def test_torneo_misma_seed_mismo_resultado() -> None:
    pob = [[1, 2, 3], [3, 2, 1], [2, 3, 1], [1, 3, 2]]
    fit = [10.0, 5.0, 7.0, 12.0]
    g1 = seleccion_torneo(pob, fit, rng=np.random.default_rng(99), k=2)
    g2 = seleccion_torneo(pob, fit, rng=np.random.default_rng(99), k=2)
    assert g1 == g2


def test_torneo_k_mayor_que_pob_se_recorta() -> None:
    pob = [[1, 2], [2, 1]]
    fit = [3.0, 1.0]
    rng = np.random.default_rng(0)
    ganador = seleccion_torneo(pob, fit, rng=rng, k=10)
    # Con k recortado a 2, el ganador es el de menor fitness.
    assert ganador == [2, 1]


# --------------------------- Order Crossover (OX) -----------------------------


@pytest.mark.parametrize("n", [5, 10, 25, 100])
def test_ox_invariantes_de_permutacion(n: int) -> None:
    rng = np.random.default_rng(1234)
    base = list(range(1, n + 1))
    padre1 = list(rng.permutation(base))
    padre2 = list(rng.permutation(base))
    hijo = cruza_ox(padre1, padre2, rng=rng)
    assert len(hijo) == n
    assert sorted(hijo) == base
    assert set(hijo) == set(padre1) == set(padre2)


def test_ox_misma_seed_mismo_hijo() -> None:
    padre1 = [1, 2, 3, 4, 5, 6, 7, 8]
    padre2 = [8, 7, 6, 5, 4, 3, 2, 1]
    h1 = cruza_ox(padre1, padre2, rng=np.random.default_rng(42))
    h2 = cruza_ox(padre1, padre2, rng=np.random.default_rng(42))
    assert h1 == h2


def test_ox_padres_identicos_devuelve_padre() -> None:
    """Si ambos padres son iguales, el hijo debe ser idéntico (no inventa genes)."""
    padre = [3, 1, 4, 1, 5, 9, 2, 6, 5, 8]  # demo: lo normalizamos
    padre = list(dict.fromkeys(padre))  # quita duplicados respetando orden
    rng = np.random.default_rng(7)
    hijo = cruza_ox(padre, padre, rng=rng)
    assert hijo == padre


def test_ox_segmento_padre1_se_preserva_en_hijo() -> None:
    """El hijo debe contener un segmento contiguo del padre1 en la misma posición."""
    padre1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    padre2 = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    rng = np.random.default_rng(0)
    hijo = cruza_ox(padre1, padre2, rng=rng)
    # Buscamos al menos un segmento de longitud >= 2 que coincida con padre1.
    n = len(padre1)
    encontro = False
    for ini in range(n):
        for fin in range(ini + 2, n + 1):
            if hijo[ini:fin] == padre1[ini:fin]:
                encontro = True
                break
        if encontro:
            break
    assert encontro, f"Hijo no preserva ningún segmento contiguo del padre1: {hijo}"


def test_ox_falla_con_padres_de_longitud_distinta() -> None:
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError, match="longitud"):
        cruza_ox([1, 2, 3], [1, 2], rng=rng)


def test_ox_falla_con_padres_de_genes_distintos() -> None:
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError, match="genes"):
        cruza_ox([1, 2, 3], [4, 5, 6], rng=rng)


def test_ox_padre_de_un_solo_gen() -> None:
    rng = np.random.default_rng(0)
    hijo = cruza_ox([1], [1], rng=rng)
    assert hijo == [1]
