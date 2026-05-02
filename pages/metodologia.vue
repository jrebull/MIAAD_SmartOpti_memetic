<template>
  <div>
    <AppHeader />
    <main class="container-prose">
      <h1>Metodología</h1>

      <h2>Paradigma híbrido GA + Tabú</h2>
      <p>
        El algoritmo memético combina exploración global mediante un
        Algoritmo Genético (selección por torneo + Order Crossover) con
        explotación local mediante Búsqueda Tabú (operador swap, tenencia
        configurable, criterio de aspiración). La mutación clásica se omite:
        la propia Tabú actúa como super-mutación inteligente.
      </p>

      <h2>Representación: Giant Tour</h2>
      <p>
        El cromosoma es una permutación
        <code>(π₁, π₂, …, π_N)</code> de los IDs de cliente. Un decodificador
        determinista (<em>Split capacitado</em>) lo recorre de izquierda a derecha
        y abre una nueva ruta cuando la siguiente demanda excedería la capacidad
        <code>Q</code> del vehículo actual. Toda permutación es así una solución
        factible.
      </p>

      <h2>Reproducibilidad bit a bit</h2>
      <p>
        Cada run se serializa con metadatos de auditoría:
        <code>git_commit_hash</code>, versiones exactas de Python y
        librerías, hash MD5 de la instancia y timestamp UTC.
        <code>scripts/verificar_reproducibilidad.py</code> re-ejecuta los runs
        en modo smoke y compara contra los resultados anteriores.
      </p>

      <h2>Ejecutar el pipeline</h2>
      <pre class="bg-ink text-mist text-xs p-4 rounded overflow-x-auto"><code>make install        # Dependencias Python
make generate-data  # Genera las 4 instancias deterministas
make experiments    # Corre los 3 escenarios × 5 seeds
make report-assets  # Figuras y tablas para LaTeX
make web-data       # Exporta JSON e imágenes para esta web
make web-build      # npm run generate</code></pre>
    </main>
    <AppFooter />
  </div>
</template>
