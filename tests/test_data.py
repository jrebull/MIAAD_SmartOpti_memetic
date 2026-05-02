"""Pruebas para el módulo de datos: generación y carga de instancias CVRP."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from memetico_cvrp.data import cargar_instancia, generar_instancia_cvrp


def test_seed_reproduce_byte_identico(tmp_path: Path) -> None:
    """Misma semilla y parámetros → mismo CSV byte por byte."""
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    generar_instancia_cvrp(num_clientes=10, capacidad=40, seed=42, output_path=a)
    generar_instancia_cvrp(num_clientes=10, capacidad=40, seed=42, output_path=b)
    assert a.read_bytes() == b.read_bytes()


def test_seeds_distintas_csv_distinto(tmp_path: Path) -> None:
    """Semillas distintas → CSVs distintos (alta probabilidad)."""
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    generar_instancia_cvrp(num_clientes=20, capacidad=50, seed=1, output_path=a)
    generar_instancia_cvrp(num_clientes=20, capacidad=50, seed=2, output_path=b)
    assert a.read_bytes() != b.read_bytes()


def test_deposito_id_cero_centro(tmp_path: Path) -> None:
    """El depósito siempre es ID 0, en (50, 50), con demanda 0."""
    out = tmp_path / "i.csv"
    generar_instancia_cvrp(num_clientes=5, capacidad=30, seed=7, output_path=out)
    ins = cargar_instancia(out)
    deposito = ins.deposito
    assert deposito.id == 0
    assert deposito.x == 50
    assert deposito.y == 50
    assert deposito.demanda == 0


def test_clientes_ids_consecutivos(tmp_path: Path) -> None:
    out = tmp_path / "i.csv"
    generar_instancia_cvrp(num_clientes=12, capacidad=50, seed=99, output_path=out)
    ins = cargar_instancia(out)
    assert sorted(ins.nodos.keys()) == list(range(0, 13))
    assert ins.num_clientes == 12


def test_meta_json_contiene_seed_y_hash(tmp_path: Path) -> None:
    out = tmp_path / "i.csv"
    generar_instancia_cvrp(
        num_clientes=8,
        capacidad=40,
        seed=2026,
        output_path=out,
        nombre_escenario="prueba",
    )
    meta_path = out.with_suffix(".meta.json")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["seed"] == 2026
    assert meta["escenario"] == "prueba"
    assert meta["num_clientes"] == 8
    assert meta["capacidad"] == 40
    assert "csv_md5" in meta
    assert len(meta["csv_md5"]) == 32  # MD5 hex


def test_validacion_demanda_excede_capacidad(tmp_path: Path) -> None:
    """Si la demanda máxima posible supera la capacidad, falla rápido."""
    out = tmp_path / "i.csv"
    with pytest.raises(ValueError, match="capacidad"):
        generar_instancia_cvrp(
            num_clientes=5,
            capacidad=10,
            seed=1,
            output_path=out,
            demand_range=(15, 20),
        )


def test_validacion_num_clientes_invalido(tmp_path: Path) -> None:
    out = tmp_path / "i.csv"
    with pytest.raises(ValueError, match="num_clientes"):
        generar_instancia_cvrp(num_clientes=0, capacidad=10, seed=1, output_path=out)


def test_cargar_falla_si_falta_deposito(tmp_path: Path) -> None:
    out = tmp_path / "i.csv"
    out.write_text(
        "ID,X,Y,Demanda\n1,10,20,5\n2,30,40,8\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="depósito"):
        cargar_instancia(out, capacidad=20)


def test_cargar_falla_columnas_invalidas(tmp_path: Path) -> None:
    out = tmp_path / "i.csv"
    out.write_text("id,x,y,demand\n0,50,50,0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Columnas"):
        cargar_instancia(out, capacidad=10)


def test_instancia_base_tutorial_reproduce(tmp_path: Path) -> None:
    """Reproduce el tutorial: seed=2026, N=25, Q=50.

    Sólo verificamos invariantes estructurales (la firma exacta del CSV se valida
    indirectamente vía `test_seed_reproduce_byte_identico`).
    """
    out = tmp_path / "instancia_base_25_q50.csv"
    generar_instancia_cvrp(
        num_clientes=25,
        capacidad=50,
        seed=2026,
        output_path=out,
        nombre_escenario="base_tutorial",
    )
    ins = cargar_instancia(out)
    assert ins.num_clientes == 25
    assert ins.capacidad == 50
    # Todas las demandas deben estar en [5, 15] por defecto.
    for nodo in ins.nodos.values():
        if not nodo.es_deposito:
            assert 5 <= nodo.demanda <= 15
            assert 10 <= nodo.x <= 90
            assert 10 <= nodo.y <= 90
