<script setup lang="ts">
const { data: resumen } = await useFetch<{
  n_escenarios: number;
  escenarios: Array<{
    id: string;
    nombre: string;
    costo_mejor?: number;
    costo_media?: number;
    costo_std?: number;
    vehiculos_mejor?: number;
    vehiculos_media?: number;
    utilizacion_pct?: number;
    tiempo_media_s?: number;
    n_runs?: number;
  }>;
}>("/data/resumen_experimentos.json", {
  default: () => ({ n_escenarios: 0, escenarios: [] }),
});
</script>

<template>
  <div>
    <AppHeader />

    <main class="container-prose">
      <header class="space-y-4">
        <span class="pill">MIAAD · UACJ · Mayo 2026</span>
        <h1>Algoritmo Memético para CVRP</h1>
        <p class="text-lg text-graphite">
          Fusión de Algoritmo Genético y Búsqueda Tabú para resolver el Problema de
          Enrutamiento de Vehículos con Capacidad. Implementado desde cero, sin
          librerías VRP externas. Tres escenarios de estrés con multi-seed.
        </p>
      </header>

      <section class="mt-12 space-y-6">
        <h2>Escenarios evaluados</h2>
        <p class="text-graphite">
          Cada escenario se ejecuta con cinco semillas
          <code>{2026, 2027, 2028, 2029, 2030}</code> y se reportan estadísticos
          agregados (mejor, media, desviación estándar, utilización promedio de la flota).
        </p>

        <div v-if="resumen.n_escenarios > 0" class="grid md:grid-cols-3 gap-5">
          <ScenarioCard
            v-for="e in resumen.escenarios"
            :key="e.id"
            :escenario="e"
          />
        </div>
        <EmptyState v-else />
      </section>

      <section v-if="resumen.n_escenarios > 0" class="mt-16 space-y-6">
        <h2>Resumen comparativo</h2>
        <ResultsTable :filas="resumen.escenarios" />
      </section>

      <section v-if="resumen.n_escenarios > 0" class="mt-16 space-y-6">
        <h2>Distribución de costos por escenario</h2>
        <figure class="card">
          <img
            src="/images/boxplot_costos.png"
            alt="Boxplot de costos finales por escenario"
            class="w-full h-auto"
            loading="lazy"
          />
          <figcaption class="text-xs text-graphite mt-3 text-center">
            Cinco runs por escenario; la caja muestra el rango intercuartil y los
            bigotes la dispersión completa.
          </figcaption>
        </figure>
      </section>

      <section class="mt-16 space-y-4">
        <h2>Reproducir desde cero</h2>
        <pre class="bg-ink text-mist text-xs p-4 rounded overflow-x-auto"><code>git clone https://github.com/jrebull/MIAAD_SmartOpti_memetic.git
cd MIAAD_SmartOpti_memetic
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make ci</code></pre>
        <p class="text-graphite text-sm">
          Detalles en <NuxtLink to="/metodologia">metodología</NuxtLink>.
        </p>
      </section>
    </main>

    <AppFooter />
  </div>
</template>
