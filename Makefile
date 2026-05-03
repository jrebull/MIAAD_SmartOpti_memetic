.PHONY: help install setup-web test test-cov lint format generate-data experiments \
        report-assets web-data web-dev web-build web-preview clean ci

help:              ## Lista los targets disponibles
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install:           ## Instala dependencias Python
	python -m pip install --upgrade pip
	pip install -r requirements.txt

setup-web:         ## Instala dependencias web (Nuxt + Tailwind)
	npm install

test:              ## Corre pruebas unitarias rápidas
	pytest -q

test-cov:          ## Corre pruebas con reporte de cobertura
	pytest --cov=src/memetico_cvrp --cov-report=term-missing

lint:              ## Linter (ruff) y type checker (mypy)
	ruff check src/ scripts/ tests/
	mypy src/memetico_cvrp/

format:            ## Formatea código con ruff
	ruff format src/ scripts/ tests/

generate-data:     ## Genera las instancias CVRP (4 escenarios)
	python scripts/generar_instancias.py

experiments:       ## Corre todos los experimentos definidos en config/experiments.yaml
	python scripts/correr_experimentos.py

report-assets:     ## Prepara figuras y tablas para el reporte LaTeX
	python scripts/preparar_reporte.py

web-data:          ## Exporta JSONs e imágenes para la web
	python scripts/exportar_resultados_web.py

playground-sync:   ## Sincroniza el paquete Python al public/playground/ (Pyodide)
	python scripts/preparar_playground.py

web-dev:           ## Servidor de desarrollo Nuxt
	npm run dev

web-build:         ## Genera estáticos para Netlify
	npm run generate

web-preview:       ## Previsualiza el build estático
	npm run preview

clean:             ## Limpia artefactos temporales (no toca data/ ni results/)
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov
	rm -rf .nuxt .output node_modules
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

ci:                ## Pipeline completo local: lint → test → datos → experimentos → assets → web
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) generate-data
	$(MAKE) experiments
	$(MAKE) report-assets
	$(MAKE) web-data
	$(MAKE) playground-sync
