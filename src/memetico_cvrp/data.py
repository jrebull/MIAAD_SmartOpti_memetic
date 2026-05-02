"""Generación, carga y validación de instancias CVRP.

Mantiene compatibilidad bit-a-bit con el tutorial base (`docs/material-base/memetic.html`):
usa el módulo `random` de stdlib con semilla fija para que dos invocaciones con la misma
semilla produzcan el mismo CSV byte por byte.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

CapacidadVehiculo = int


@dataclass(frozen=True)
class Nodo:
    """Nodo del grafo CVRP. El depósito siempre es ID 0 con demanda 0."""

    id: int
    x: float
    y: float
    demanda: int

    @property
    def es_deposito(self) -> bool:
        return self.id == 0


@dataclass(frozen=True)
class Instancia:
    """Instancia CVRP completa: nodos + capacidad."""

    nodos: dict[int, Nodo]
    capacidad: CapacidadVehiculo
    nombre: str = "custom"
    seed: int | None = None
    metadatos: dict = field(default_factory=dict)

    @property
    def num_clientes(self) -> int:
        return len(self.nodos) - 1  # excluye depósito

    @property
    def deposito(self) -> Nodo:
        return self.nodos[0]


def generar_instancia_cvrp(
    num_clientes: int,
    capacidad: CapacidadVehiculo,
    seed: int,
    output_path: str | Path,
    *,
    x_range: tuple[int, int] = (10, 90),
    y_range: tuple[int, int] = (10, 90),
    demand_range: tuple[int, int] = (5, 15),
    nombre_escenario: str = "custom",
) -> Path:
    """Genera una instancia CVRP determinista y la persiste en CSV + .meta.json.

    El depósito es siempre el nodo 0 con coordenadas (50, 50) y demanda 0. Los clientes
    tienen IDs consecutivos 1..N con coordenadas y demandas enteras uniformes en los
    rangos provistos.

    Reproducibilidad: usa `random.Random(seed)` (stdlib) para coincidir bit-a-bit con
    la generación del tutorial (`memetic.html`).

    Parameters
    ----------
    num_clientes
        Cantidad de clientes a generar (no incluye el depósito).
    capacidad
        Capacidad máxima de cada vehículo de la flota homogénea.
    seed
        Semilla determinista. Misma semilla → mismo CSV byte por byte.
    output_path
        Ruta del archivo CSV de salida. Se crea junto un `.meta.json` con metadatos.
    x_range, y_range
        Rango (inclusivo) de coordenadas en el plano.
    demand_range
        Rango (inclusivo) de demandas por cliente.
    nombre_escenario
        Etiqueta humana para identificar el escenario en el `.meta.json`.

    Returns
    -------
    Path
        Ruta del CSV generado.

    Raises
    ------
    ValueError
        Si los rangos son inválidos o si la capacidad no puede acomodar la demanda
        máxima posible.
    """
    if num_clientes < 1:
        raise ValueError(f"num_clientes debe ser >= 1, recibido {num_clientes}")
    if capacidad < demand_range[1]:
        raise ValueError(
            f"capacidad={capacidad} es menor que la demanda máxima posible "
            f"{demand_range[1]}: ningún cliente con demanda máxima cabría en un vehículo."
        )
    if x_range[0] > x_range[1] or y_range[0] > y_range[1] or demand_range[0] > demand_range[1]:
        raise ValueError("Rangos inválidos: el límite inferior debe ser <= superior.")

    rng = random.Random(seed)

    datos: list[dict] = [{"ID": 0, "X": 50, "Y": 50, "Demanda": 0}]
    for i in range(1, num_clientes + 1):
        x = rng.randint(x_range[0], x_range[1])
        y = rng.randint(y_range[0], y_range[1])
        demanda = rng.randint(demand_range[0], demand_range[1])
        datos.append({"ID": i, "X": x, "Y": y, "Demanda": demanda})

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ID", "X", "Y", "Demanda"])
        writer.writeheader()
        writer.writerows(datos)

    meta_path = output_path.with_suffix(".meta.json")
    meta = {
        "escenario": nombre_escenario,
        "num_clientes": num_clientes,
        "capacidad": capacidad,
        "seed": seed,
        "x_range": list(x_range),
        "y_range": list(y_range),
        "demand_range": list(demand_range),
        "csv_md5": _hash_archivo(output_path),
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return output_path


def cargar_instancia(
    path: str | Path,
    capacidad: CapacidadVehiculo | None = None,
    *,
    nombre: str = "instancia",
) -> Instancia:
    """Carga una instancia CVRP desde un CSV y opcionalmente su `.meta.json`.

    Parameters
    ----------
    path
        Ruta del CSV (columnas: ID, X, Y, Demanda).
    capacidad
        Si se provee, sobreescribe la capacidad del `.meta.json`. Si ninguno está
        disponible, se levanta `ValueError`.
    nombre
        Etiqueta humana para el escenario (sólo si no hay `.meta.json`).

    Returns
    -------
    Instancia

    Raises
    ------
    FileNotFoundError, ValueError
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No existe la instancia: {path}")

    nodos: dict[int, Nodo] = {}
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = set(reader.fieldnames or [])
        if cols != {"ID", "X", "Y", "Demanda"}:
            raise ValueError(
                f"Columnas inesperadas en {path}: {sorted(cols)}. "
                "Se esperan exactamente: ID, X, Y, Demanda."
            )
        for row in reader:
            nid = int(row["ID"])
            nodos[nid] = Nodo(
                id=nid,
                x=float(row["X"]),
                y=float(row["Y"]),
                demanda=int(row["Demanda"]),
            )

    if 0 not in nodos:
        raise ValueError(f"La instancia {path} no contiene depósito (ID 0).")
    if nodos[0].demanda != 0:
        raise ValueError(f"El depósito debe tener demanda 0, tiene {nodos[0].demanda}.")

    suma_demandas = sum(n.demanda for n in nodos.values())
    if suma_demandas <= 0:
        raise ValueError(f"Suma de demandas no positiva: {suma_demandas}.")

    metadatos: dict = {}
    seed: int | None = None
    nombre_efectivo = nombre
    capacidad_efectiva = capacidad

    meta_path = path.with_suffix(".meta.json")
    if meta_path.exists():
        metadatos = json.loads(meta_path.read_text(encoding="utf-8"))
        if capacidad_efectiva is None:
            capacidad_efectiva = int(metadatos.get("capacidad"))
        seed = metadatos.get("seed")
        nombre_efectivo = metadatos.get("escenario", nombre)

    if capacidad_efectiva is None:
        raise ValueError(
            f"No se pudo determinar la capacidad para {path}: "
            "pasa el parámetro `capacidad` o asegúrate que exista el .meta.json."
        )

    max_dem = max(n.demanda for n in nodos.values())
    if max_dem > capacidad_efectiva:
        raise ValueError(
            f"Cliente con demanda {max_dem} excede la capacidad del vehículo "
            f"{capacidad_efectiva}. La instancia es inviable."
        )

    return Instancia(
        nodos=nodos,
        capacidad=capacidad_efectiva,
        nombre=nombre_efectivo,
        seed=seed,
        metadatos=metadatos,
    )


def _hash_archivo(path: Path) -> str:
    """Devuelve el MD5 hexadecimal del archivo (para el manifiesto de reproducibilidad)."""
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
