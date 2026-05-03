"""Validador blindado de soluciones CVRP.

Auditoría de extremo a extremo: verifica que toda solución reportada cumpla
las tres restricciones duras del CVRP y que su costo coincida con el recalculado
por nosotros (no se confía en lo que el algoritmo dice).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from memetico_cvrp.data import Nodo


class SolucionInvalidaError(ValueError):
    """Se levanta cuando una solución no pasa la validación."""


@dataclass
class ValidacionResultado:
    """Resultado positivo de validación. Contiene métricas verificables."""

    factible: bool
    costo_recalculado: float
    num_vehiculos: int
    cargas: list[int]
    utilizacion_pct: float
    detalles: dict = field(default_factory=dict)


def validar_solucion(
    rutas: list[list[int]],
    nodos: dict[int, Nodo],
    capacidad: int,
    distancia_reportada: float | None = None,
    *,
    tolerancia: float = 1e-6,
    dist_matriz: np.ndarray | None = None,
) -> ValidacionResultado:
    """Valida que una solución CVRP es factible y que su costo es real.

    Comprobaciones:
    1. Toda ruta inicia y termina en el depósito (ID 0).
    2. Cada cliente `1..N` aparece exactamente una vez globalmente.
    3. Ninguna ruta excede la capacidad `Q`.
    4. (Opcional) El costo recalculado coincide con `distancia_reportada`
       dentro de la tolerancia.

    Parameters
    ----------
    rutas
        Lista de rutas; cada ruta es una lista que empieza y termina en 0.
    nodos
        Diccionario `{id: Nodo}` con demandas.
    capacidad
        `Q`: capacidad de la flota homogénea.
    distancia_reportada
        Si se provee, se compara contra el costo recalculado.
    tolerancia
        Margen absoluto admisible al comparar costos en `float`.
    dist_matriz
        Matriz precalculada. Si es `None`, se construye internamente.

    Returns
    -------
    ValidacionResultado
        Métricas verificables: costo, vehículos, cargas, utilización %.

    Raises
    ------
    SolucionInvalidaError
        Si alguna comprobación falla. El mensaje detalla qué falló.
    """
    if not rutas:
        raise SolucionInvalidaError("La solución no contiene ninguna ruta.")

    clientes_esperados = set(range(1, len(nodos)))

    # 1. Inicio y fin en depósito.
    for k, ruta in enumerate(rutas, start=1):
        if not ruta or ruta[0] != 0 or ruta[-1] != 0:
            raise SolucionInvalidaError(
                f"Ruta {k} no inicia y/o no termina en el depósito (0): {ruta[:6]}..."
            )
        if len(ruta) < 2:
            raise SolucionInvalidaError(f"Ruta {k} demasiado corta: {ruta}")

    # 2. Cobertura única.
    visitados: list[int] = []
    for ruta in rutas:
        visitados.extend([c for c in ruta if c != 0])

    if len(visitados) != len(set(visitados)):
        duplicados = sorted({c for c in visitados if visitados.count(c) > 1})
        raise SolucionInvalidaError(
            f"Clientes visitados más de una vez: {duplicados[:10]}"
        )

    visitados_set = set(visitados)
    faltantes = clientes_esperados - visitados_set
    extras = visitados_set - clientes_esperados
    if faltantes:
        raise SolucionInvalidaError(f"Clientes faltantes en la solución: {sorted(faltantes)[:10]}")
    if extras:
        raise SolucionInvalidaError(
            f"IDs de cliente fuera del rango 1..N en la solución: {sorted(extras)[:10]}"
        )

    # 3. Capacidad por ruta.
    cargas: list[int] = []
    for k, ruta in enumerate(rutas, start=1):
        carga = sum(nodos[c].demanda for c in ruta if c != 0)
        if carga > capacidad:
            raise SolucionInvalidaError(
                f"Ruta {k} excede capacidad: carga={carga} > Q={capacidad}"
            )
        cargas.append(carga)

    # 4. Recalcular costo.
    if dist_matriz is None:
        from memetico_cvrp.distance import calcular_matriz_distancias

        dist_matriz = calcular_matriz_distancias(nodos)

    costo_recalc = 0.0
    for ruta in rutas:
        for i in range(len(ruta) - 1):
            costo_recalc += float(dist_matriz[ruta[i], ruta[i + 1]])

    if distancia_reportada is not None and abs(costo_recalc - distancia_reportada) > tolerancia:
        raise SolucionInvalidaError(
            f"Distancia reportada ({distancia_reportada:.6f}) no coincide con la "
            f"recalculada ({costo_recalc:.6f}); diferencia="
            f"{abs(costo_recalc - distancia_reportada):.2e} > tol={tolerancia:.2e}"
        )

    capacidad_total_ofertada = capacidad * len(rutas)
    demanda_atendida = sum(cargas)
    utilizacion = 100.0 * demanda_atendida / capacidad_total_ofertada if capacidad_total_ofertada else 0.0

    return ValidacionResultado(
        factible=True,
        costo_recalculado=costo_recalc,
        num_vehiculos=len(rutas),
        cargas=cargas,
        utilizacion_pct=utilizacion,
        detalles={
            "demanda_atendida": demanda_atendida,
            "capacidad_total_ofertada": capacidad_total_ofertada,
        },
    )
