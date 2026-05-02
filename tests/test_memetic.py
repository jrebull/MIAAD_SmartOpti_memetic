"""Pruebas del orquestador memético: factibilidad, monotonía y reproducibilidad."""

from __future__ import annotations

from pathlib import Path

import pytest

from memetico_cvrp.data import cargar_instancia, generar_instancia_cvrp
from memetico_cvrp.distance import calcular_matriz_distancias
from memetico_cvrp.memetic import ConfigMemetico, algoritmo_memetico
from memetico_cvrp.split import evaluar_cromosoma


@pytest.fixture
def instancia_chica(tmp_path: Path):
    out = tmp_path / "i.csv"
    generar_instancia_cvrp(num_clientes=15, capacidad=40, seed=2026, output_path=out)
    ins = cargar_instancia(out)
    return ins


def test_resultado_es_factible(instancia_chica) -> None:
    config = ConfigMemetico(
        generaciones=10,
        tamano_poblacion=20,
        torneo_k=3,
        prob_tabu=0.5,
        iter_tabu=10,
        tenencia=5,
        sample_size=10,
        seed=42,
        capacidad=instancia_chica.capacidad,
    )
    res = algoritmo_memetico(instancia_chica.nodos, config)
    # Permutación válida.
    assert sorted(res.mejor_cromosoma) == list(range(1, instancia_chica.num_clientes + 1))
    # Decodificación factible.
    split = evaluar_cromosoma(
        res.mejor_cromosoma,
        calcular_matriz_distancias(instancia_chica.nodos),
        instancia_chica.nodos,
        instancia_chica.capacidad,
    )
    for carga in split.cargas:
        assert carga <= instancia_chica.capacidad
    for ruta in split.rutas:
        assert ruta[0] == 0 and ruta[-1] == 0


def test_costo_no_aumenta_entre_generaciones_por_elitismo(instancia_chica) -> None:
    config = ConfigMemetico(
        generaciones=15,
        tamano_poblacion=20,
        torneo_k=3,
        prob_tabu=0.4,
        iter_tabu=10,
        tenencia=5,
        sample_size=10,
        seed=11,
        capacidad=instancia_chica.capacidad,
    )
    res = algoritmo_memetico(instancia_chica.nodos, config)
    h = res.historico_convergencia
    # Histórico del mejor global: monótonamente no creciente.
    for i in range(1, len(h)):
        assert h[i] <= h[i - 1] + 1e-9


def test_seed_reproduce_resultado(instancia_chica) -> None:
    config = ConfigMemetico(
        generaciones=8,
        tamano_poblacion=15,
        torneo_k=3,
        prob_tabu=0.5,
        iter_tabu=8,
        tenencia=5,
        sample_size=8,
        seed=2026,
        capacidad=instancia_chica.capacidad,
    )
    a = algoritmo_memetico(instancia_chica.nodos, config)
    b = algoritmo_memetico(instancia_chica.nodos, config)
    assert a.mejor_cromosoma == b.mejor_cromosoma
    assert a.costo_final == pytest.approx(b.costo_final)
    assert a.historico_convergencia == b.historico_convergencia


def test_seeds_distintas_producen_resultados_distintos(instancia_chica) -> None:
    """Es muy improbable (no garantizado) que dos seeds lleguen al mismo cromosoma."""
    base = ConfigMemetico(
        generaciones=8,
        tamano_poblacion=15,
        torneo_k=3,
        prob_tabu=0.5,
        iter_tabu=8,
        tenencia=5,
        sample_size=8,
        seed=1,
        capacidad=instancia_chica.capacidad,
    )
    otro = ConfigMemetico(**{**base.__dict__, "seed": 2})
    a = algoritmo_memetico(instancia_chica.nodos, base)
    b = algoritmo_memetico(instancia_chica.nodos, otro)
    # Al menos una de las trayectorias o cromosomas debe diferir.
    assert (
        a.mejor_cromosoma != b.mejor_cromosoma
        or a.historico_convergencia != b.historico_convergencia
    )


def test_validacion_config() -> None:
    with pytest.raises(ValueError, match="generaciones"):
        ConfigMemetico(generaciones=0).validar()
    with pytest.raises(ValueError, match="tamano_poblacion"):
        ConfigMemetico(tamano_poblacion=1).validar()
    with pytest.raises(ValueError, match="prob_tabu"):
        ConfigMemetico(prob_tabu=1.5).validar()


def test_metricas_resultado(instancia_chica) -> None:
    config = ConfigMemetico(
        generaciones=5,
        tamano_poblacion=10,
        torneo_k=3,
        prob_tabu=0.4,
        iter_tabu=8,
        tenencia=3,
        sample_size=6,
        seed=7,
        capacidad=instancia_chica.capacidad,
    )
    res = algoritmo_memetico(instancia_chica.nodos, config)
    assert res.tiempo_ejecucion > 0
    assert len(res.historico_convergencia) == config.generaciones + 1
    assert len(res.historico_promedio) == config.generaciones + 1
    assert 0 <= res.generacion_mejor <= config.generaciones
    assert res.iteraciones_tabu_aplicadas >= 0
    assert res.aceptaciones_no_mejorantes_tabu >= 0
