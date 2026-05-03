<script setup lang="ts">
import resumen from "~/assets/data/resumen_experimentos.json";

const stats = [
  { valor: "3", etiqueta: "Escenarios" },
  { valor: "15", etiqueta: "Runs (multi-seed)" },
  { valor: "84", etiqueta: "Tests verdes" },
  { valor: "100 %", etiqueta: "Factibilidad" },
];
</script>

<template>
  <div>
    <AppHeader />

    <!-- HERO -->
    <section class="relative overflow-hidden border-b border-slate-100">
      <div
        class="absolute inset-0 -z-10 opacity-[0.04]"
        :style="{
          backgroundImage:
            'linear-gradient(to right, #1A2130 1px, transparent 1px), linear-gradient(to bottom, #1A2130 1px, transparent 1px)',
          backgroundSize: '32px 32px',
        }"
      />
      <div class="absolute -top-32 -right-20 w-96 h-96 -z-10 rounded-full bg-sky/10 blur-3xl" />
      <div class="absolute -bottom-20 -left-20 w-80 h-80 -z-10 rounded-full bg-graphite/10 blur-3xl" />

      <div class="max-w-5xl mx-auto px-6 md:px-8 py-20 md:py-28">
        <span class="pill">MIAAD · UACJ · Mayo 2026</span>
        <h1 class="mt-5 text-4xl md:text-6xl font-bold tracking-tight leading-[1.05]">
          Algoritmo Memético<br />
          <span class="text-graphite">para CVRP</span>
        </h1>
        <p class="mt-6 max-w-2xl text-lg md:text-xl text-graphite leading-relaxed">
          Fusión de <strong class="text-ink">Algoritmo Genético</strong> y
          <strong class="text-ink">Búsqueda Tabú</strong> para resolver el Problema de
          Enrutamiento de Vehículos con Capacidad. Implementado desde cero, sin librerías
          VRP externas. Tres escenarios de estrés con multi-seed y reproducibilidad
          bit-a-bit.
        </p>
        <div class="mt-8 flex flex-wrap gap-3">
          <NuxtLink
            to="/playground"
            class="inline-flex items-center gap-2 px-5 py-2.5 bg-ink text-white rounded text-sm font-medium hover:bg-graphite transition-colors no-underline"
          >
            Probar el algoritmo en vivo
            <span aria-hidden="true">→</span>
          </NuxtLink>
          <NuxtLink
            to="/escenarios"
            class="inline-flex items-center gap-2 px-5 py-2.5 border border-slate-300 text-ink rounded text-sm font-medium hover:border-ink transition-colors no-underline"
          >
            Ver resultados
          </NuxtLink>
          <NuxtLink
            to="/codigo"
            class="inline-flex items-center gap-2 px-5 py-2.5 text-graphite rounded text-sm font-medium hover:text-ink transition-colors no-underline"
          >
            Leer el código
          </NuxtLink>
        </div>

        <!-- Stats -->
        <div class="mt-14 grid grid-cols-2 md:grid-cols-4 gap-px bg-slate-200 rounded-xl overflow-hidden">
          <div
            v-for="s in stats"
            :key="s.etiqueta"
            class="bg-white px-5 py-6"
          >
            <p class="text-3xl md:text-4xl font-bold text-ink font-mono leading-none">
              {{ s.valor }}
            </p>
            <p class="mt-2 text-xs uppercase tracking-wider text-graphite">{{ s.etiqueta }}</p>
          </div>
        </div>
      </div>
    </section>

    <main class="container-prose">
      <!-- Escenarios -->
      <section class="mt-4">
        <header class="flex items-baseline justify-between mb-6">
          <h2 class="!mt-0">Escenarios evaluados</h2>
          <NuxtLink to="/escenarios" class="text-sm text-graphite hover:text-ink">
            ver todos →
          </NuxtLink>
        </header>
        <p class="text-graphite mb-6">
          Cada escenario se ejecuta con cinco semillas
          <code>{2026, 2027, 2028, 2029, 2030}</code> y se reportan estadísticos
          agregados. Las soluciones pasan validación de factibilidad antes de
          publicarse.
        </p>

        <div v-if="resumen.n_escenarios > 0" class="grid md:grid-cols-3 gap-5">
          <ScenarioCard v-for="e in resumen.escenarios" :key="e.id" :escenario="e" />
        </div>
        <EmptyState v-else />
      </section>

      <!-- Tabla resumen -->
      <section v-if="resumen.n_escenarios > 0" class="mt-16">
        <h2>Resumen comparativo</h2>
        <p class="text-graphite mb-4">
          Costo final = distancia euclidiana total recorrida por todos los vehículos.
          Utilización = demanda atendida / capacidad ofertada.
        </p>
        <ResultsTable :filas="resumen.escenarios" />
      </section>

      <!-- Boxplot -->
      <section v-if="resumen.n_escenarios > 0" class="mt-16">
        <h2>Distribución de costos</h2>
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

      <!-- CTA Reproducir -->
      <section class="mt-16">
        <h2>Reproducir desde cero</h2>
        <pre class="bg-ink text-mist text-xs p-4 rounded overflow-x-auto"><code>git clone https://github.com/jrebull/MIAAD_SmartOpti_memetic.git
cd MIAAD_SmartOpti_memetic
python3 -m venv .venv &amp;&amp; source .venv/bin/activate
pip install -r requirements.txt &amp;&amp; pip install -e .
make ci</code></pre>
        <p class="text-graphite text-sm mt-3">
          Detalles en <NuxtLink to="/metodologia">metodología</NuxtLink> y
          <a
            href="https://github.com/jrebull/MIAAD_SmartOpti_memetic/blob/main/docs/REPRODUCIBILITY.md"
            target="_blank"
            rel="noopener"
          >
            REPRODUCIBILITY.md
          </a>.
        </p>
      </section>
    </main>

    <AppFooter />
  </div>
</template>
