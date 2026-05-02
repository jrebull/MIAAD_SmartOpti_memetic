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
      <h1>Escenarios</h1>
      <p class="text-graphite">
        Tres instancias CVRP deterministas, cada una con cinco runs.
      </p>

      <section class="mt-10 grid md:grid-cols-3 gap-5">
        <ScenarioCard
          v-for="e in resumen.escenarios"
          :key="e.id"
          :escenario="e"
        />
        <EmptyState v-if="resumen.n_escenarios === 0" />
      </section>
    </main>
    <AppFooter />
  </div>
</template>
