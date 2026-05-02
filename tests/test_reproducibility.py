"""Pruebas de reproducibilidad: dos runs con misma seed → idénticos."""

from __future__ import annotations

from pathlib import Path

import pytest

from memetico_cvrp.data import cargar_instancia, generar_instancia_cvrp
from memetico_cvrp.io_utils import dump_run, reproducir_run
from memetico_cvrp.memetic import ConfigMemetico, algoritmo_memetico


@pytest.fixture
def setup_chico(tmp_path: Path):
    inst_path = tmp_path / "i.csv"
    generar_instancia_cvrp(num_clientes=12, capacidad=40, seed=2026, output_path=inst_path)
    inst = cargar_instancia(inst_path)
    cfg = ConfigMemetico(
        generaciones=8,
        tamano_poblacion=15,
        torneo_k=3,
        prob_tabu=0.4,
        iter_tabu=8,
        tenencia=4,
        sample_size=8,
        seed=42,
        capacidad=inst.capacidad,
    )
    return inst, inst_path, cfg


def test_dos_runs_misma_seed_iguales(setup_chico) -> None:
    inst, _, cfg = setup_chico
    a = algoritmo_memetico(inst.nodos, cfg)
    b = algoritmo_memetico(inst.nodos, cfg)
    assert a.mejor_cromosoma == b.mejor_cromosoma
    assert a.costo_final == pytest.approx(b.costo_final, abs=1e-9)


def test_seeds_distintas_resultados_distintos(setup_chico) -> None:
    inst, _, cfg = setup_chico
    cfg2 = ConfigMemetico(**{**cfg.__dict__, "seed": cfg.seed + 1})
    a = algoritmo_memetico(inst.nodos, cfg)
    b = algoritmo_memetico(inst.nodos, cfg2)
    # Improbable que coincidan exactamente.
    assert (
        a.mejor_cromosoma != b.mejor_cromosoma
        or a.historico_convergencia != b.historico_convergencia
    )


def test_dump_y_reproducir_run(setup_chico, tmp_path: Path) -> None:
    inst, inst_path, cfg = setup_chico
    res = algoritmo_memetico(inst.nodos, cfg)
    out_dir = tmp_path / "results" / "test"
    json_path = dump_run(res, output_dir=out_dir, seed=cfg.seed, instancia_path=inst_path)
    assert json_path.exists()

    # Reproducir el run debe dar el mismo costo y cromosoma.
    res2 = reproducir_run(json_path)
    assert res2.mejor_cromosoma == res.mejor_cromosoma
    assert res2.costo_final == pytest.approx(res.costo_final, abs=1e-9)
