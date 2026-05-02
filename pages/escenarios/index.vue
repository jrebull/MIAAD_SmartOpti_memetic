<script setup lang="ts">
import resumen from "~/assets/data/resumen_experimentos.json";
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
