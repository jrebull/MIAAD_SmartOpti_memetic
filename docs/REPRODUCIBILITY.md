# Reproducibilidad

Este proyecto está diseñado para que cualquier tercero pueda reproducir los
resultados del reporte **bit a bit** desde una máquina nueva.

## Garantías

- Toda fuente de aleatoriedad usa `np.random.Generator` con semilla explícita
  inyectada (excepto la generación de instancias, que usa `random.Random(seed)`
  para coincidir con el tutorial base).
- Las instancias CVRP se persisten en `data/raw/*.csv` con su `.meta.json`
  (que incluye hash MD5 y la semilla con la que se generaron).
- Cada `run_seed<N>.json` incluye metadatos completos: `git_commit_hash`,
  `python`, `numpy`, `scipy`, `matplotlib`, hash MD5 de la instancia,
  timestamp UTC.
- El script `scripts/verificar_reproducibilidad.py` re-ejecuta el pipeline en
  modo *smoke* y compara contra los resultados versionados.

## Cómo verificar los resultados del reporte

```bash
git clone https://github.com/jrebull/MIAAD_SmartOpti_memetic.git
cd MIAAD_SmartOpti_memetic
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Verificar instancias y un run por experimento.
python scripts/verificar_reproducibilidad.py --seeds-por-exp 1
```

Si todo está consistente verás `✓ Reproducibilidad verificada.` y se generará
`data/results/MANIFEST.json` con el resumen.

## Cómo reproducir desde cero (todos los experimentos)

```bash
make install         # dependencias Python
make generate-data   # 4 instancias deterministas en data/raw/
make experiments     # 3 escenarios x 5 seeds en data/results/
make report-assets   # figuras y tablas LaTeX
make web-data        # JSON e imágenes para la web
make test            # corre la suite (~84 tests)
make lint            # ruff
```

## Tiempos aproximados (referencia)

Hardware de referencia: MacBook con macOS 25.5, Python 3.14.

| Experimento | Seeds | Tiempo aprox. por seed | Tiempo total |
|-------------|------:|-----------------------:|-------------:|
| Caso 1 (N=50, gen=100)  | 5 | ~30 s   | ~2.5 min |
| Caso 2 (N=100, gen=150) | 5 | ~80–120 s | ~7–10 min |
| Caso 3 (N=75, gen=100)  | 5 | ~50 s   | ~4 min  |
| **Total campaña**       |   |         | **~15 min** |

## Cuando algo cambia y necesitas re-validar

- Si modificas el código de un módulo crítico (`split.py`, `genetic.py`,
  `tabu.py`, `memetic.py`), corre `make test && make experiments` antes de
  considerar que los resultados anteriores siguen siendo válidos.
- Si modificas una instancia (cosa que no debería pasar: están versionadas y
  son deterministas), `verificar_reproducibilidad.py` levantará error porque
  el MD5 dejará de coincidir.

## Notas conocidas

- La reproducibilidad bit a bit aplica a la **misma versión de NumPy y la
  misma plataforma**. Cambios mayores en NumPy podrían alterar el orden de
  generación de números pseudo-aleatorios. Si esto pasa, `verificar_reproducibilidad.py`
  lo detectará y exigirá regenerar todos los `run_seed*.json`.
