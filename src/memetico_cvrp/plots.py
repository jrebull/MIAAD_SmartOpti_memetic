"""Visualizaciones del Algoritmo Memético: convergencia, rutas y boxplots.

Todas las figuras son sobrias, académicas y exportadas a PNG 300dpi sin emojis.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from memetico_cvrp.data import Nodo

# Paleta sobria académica alineada con la paleta del HTML base / Tailwind.
PALETA = ["#1A2130", "#5A72A0", "#83B4FF", "#B6CCE0", "#3D5A80", "#FF7F50", "#2E8B57", "#8B5A8C"]


def _aplicar_estilo() -> None:
    plt.rcParams.update(
        {
            "font.family": ["Helvetica", "Arial", "sans-serif"],
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "grid.alpha": 0.25,
            "figure.dpi": 110,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.facecolor": "white",
        }
    )


def plot_convergencia(
    historicos: list[list[float]],
    titulo: str,
    output_path: str | Path,
    *,
    etiquetas_seeds: list[int] | None = None,
) -> Path:
    """Gráfica de convergencia del mejor global por generación.

    Si hay múltiples runs, dibuja: media (línea sólida) ± 1 std (banda) y cada
    run en línea fina con baja opacidad.
    """
    _aplicar_estilo()
    fig, ax = plt.subplots(figsize=(8, 4.5))

    if not historicos:
        raise ValueError("Lista de históricos vacía.")

    arr = np.array([np.array(h) for h in historicos])
    n_gen = arr.shape[1]
    eje_x = np.arange(n_gen)

    if len(historicos) == 1:
        ax.plot(eje_x, arr[0], color=PALETA[1], lw=2, label="Mejor global")
    else:
        media = arr.mean(axis=0)
        std = arr.std(axis=0)
        for i, h in enumerate(arr):
            ax.plot(eje_x, h, color=PALETA[3], lw=0.8, alpha=0.55,
                    label=f"seed {etiquetas_seeds[i]}" if etiquetas_seeds and i == 0 else None)
        ax.fill_between(eje_x, media - std, media + std,
                        color=PALETA[1], alpha=0.18, label="±1 std")
        ax.plot(eje_x, media, color=PALETA[0], lw=2.2, label=f"Media (n={len(historicos)})")

    ax.set_xlabel("Generación")
    ax.set_ylabel("Costo (distancia total)")
    ax.set_title(titulo)
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(loc="best", frameon=False)
    fig.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_rutas(
    nodos: dict[int, Nodo],
    rutas: list[list[int]],
    cargas: list[int],
    titulo: str,
    output_path: str | Path,
    capacidad: int,
) -> Path:
    """Dibuja las rutas en el plano cartesiano (depósito como triángulo, clientes como puntos)."""
    _aplicar_estilo()
    fig, ax = plt.subplots(figsize=(7, 7))

    n_clientes = len(nodos) - 1
    etiquetar_cliente_si = (
        (lambda nid: True) if n_clientes <= 50 else (lambda nid: nid % 5 == 0 and nid != 0)
    )

    # Clientes (fondo).
    xs = [nodos[i].x for i in range(1, n_clientes + 1)]
    ys = [nodos[i].y for i in range(1, n_clientes + 1)]
    ax.scatter(xs, ys, s=22, color="#6F7B8B", alpha=0.5, zorder=2)

    # Depósito.
    deposito = nodos[0]
    ax.scatter([deposito.x], [deposito.y], s=200, marker="^", color="#1A2130",
               edgecolors="white", linewidths=1.5, zorder=5, label="Depósito")

    for k, ruta in enumerate(rutas):
        color = PALETA[(k + 1) % len(PALETA)]
        rx = [nodos[c].x for c in ruta]
        ry = [nodos[c].y for c in ruta]
        ax.plot(rx, ry, color=color, lw=1.6, alpha=0.85,
                label=f"Ruta {k + 1} — {cargas[k]}/{capacidad}")
        ax.scatter(rx[1:-1], ry[1:-1], s=42, color=color, zorder=4, edgecolors="white", linewidths=0.6)

    if n_clientes <= 50:
        for i in range(1, n_clientes + 1):
            if etiquetar_cliente_si(i):
                ax.annotate(str(i), (nodos[i].x, nodos[i].y), xytext=(4, 4),
                            textcoords="offset points", fontsize=8, color="#33415A")

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title(titulo)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), borderaxespad=0,
              fontsize=8, frameon=False)
    fig.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_boxplot_costos(
    costos_por_escenario: dict[str, list[float]],
    titulo: str,
    output_path: str | Path,
) -> Path:
    """Box-plot comparativo de los costos finales por escenario."""
    _aplicar_estilo()
    fig, ax = plt.subplots(figsize=(8, 4.8))

    nombres = list(costos_por_escenario.keys())
    datos = [costos_por_escenario[n] for n in nombres]
    bp = ax.boxplot(datos, tick_labels=nombres, patch_artist=True, widths=0.55, showmeans=True)
    for patch, color in zip(bp["boxes"], PALETA[1:]):
        patch.set_facecolor(color)
        patch.set_alpha(0.55)
    for median in bp["medians"]:
        median.set_color("#1A2130")
        median.set_linewidth(1.8)

    ax.set_ylabel("Costo (distancia total)")
    ax.set_title(titulo)
    ax.grid(True, axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def tabla_rutas_dataframe(rutas: list[list[int]], cargas: list[int],
                          capacidad: int, dist: np.ndarray) -> list[dict[str, Any]]:
    """Devuelve una lista de filas (dicts) con info de cada ruta."""
    filas: list[dict[str, Any]] = []
    for k, (ruta, carga) in enumerate(zip(rutas, cargas), start=1):
        distancia = float(sum(dist[ruta[i], ruta[i + 1]] for i in range(len(ruta) - 1)))
        filas.append(
            {
                "vehiculo": k,
                "secuencia": " → ".join(map(str, ruta)),
                "num_clientes": len(ruta) - 2,
                "carga": int(carga),
                "capacidad": int(capacidad),
                "utilizacion_pct": round(100.0 * carga / capacidad, 1),
                "distancia_ruta": round(distancia, 2),
            }
        )
    return filas


def tabla_rutas_a_latex(filas: list[dict[str, Any]], titulo: str = "Rutas") -> str:
    """Convierte la tabla de rutas en un fragmento LaTeX `tabular`."""
    lineas = [
        "\\begin{table}[H]",
        "\\centering",
        f"\\caption{{{titulo}}}",
        "\\begin{tabular}{rlrrrrr}",
        "\\toprule",
        "Veh. & Secuencia & Clientes & Carga & Cap. & Útil.\\% & Distancia \\\\",
        "\\midrule",
    ]
    for f in filas:
        secuencia = f["secuencia"].replace("→", "$\\to$")
        lineas.append(
            f"{f['vehiculo']} & {secuencia} & {f['num_clientes']} & {f['carga']} & "
            f"{f['capacidad']} & {f['utilizacion_pct']:.1f} & {f['distancia_ruta']:.2f} \\\\"
        )
    lineas += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    return "\n".join(lineas)
