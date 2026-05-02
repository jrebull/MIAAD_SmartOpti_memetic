<script setup lang="ts">
const route = useRoute();
const id = String(route.params.id);

interface MejorRun {
  seed: number;
  costo_final: number;
  num_vehiculos: number;
  rutas: number[][];
  cargas: number[];
  configuracion: Record<string, unknown>;
  tiempo_ejecucion: number;
  generacion_mejor: number;
}

interface Detalle {
  id: string;
  nombre: string;
  instancia?: string;
  capacidad?: number;
  n_runs?: number;
  costo?: { min?: number; max?: number; media?: number; mediana?: number; std?: number };
  vehiculos?: { min?: number; max?: number; media?: number; mediana?: number; std?: number };
  tiempo_segundos?: { media?: number };
  utilizacion_promedio_pct?: number;
  parametros?: Record<string, unknown>;
  demanda_total_instancia?: number;
  mejor_run?: MejorRun;
}

const { data: detalle, error } = await useFetch<Detalle>(`/data/${id}.json`, {
  default: () => null,
});

function fmt(x?: number, dec = 2): string {
  if (x === undefined || x === null || isNaN(x as number)) return "—";
  return Number(x).toFixed(dec);
}
</script>

<template>
  <div>
    <AppHeader />

    <main class="container-prose" v-if="detalle">
      <header class="space-y-3">
        <NuxtLink to="/escenarios" class="text-sm text-graphite no-underline hover:text-ink">← Escenarios</NuxtLink>
        <h1>{{ detalle.nombre }}</h1>
        <div class="flex gap-2 flex-wrap">
          <span class="pill">{{ detalle.id }}</span>
          <span class="pill">N = {{ (detalle.demanda_total_instancia ?? 0) > 0 ? "" : "" }}</span>
          <span class="pill">Q = {{ detalle.capacidad }}</span>
          <span class="pill">{{ detalle.n_runs }} runs</span>
        </div>
      </header>

      <section class="mt-10 grid md:grid-cols-2 gap-6">
        <div class="card space-y-4">
          <h3 class="!mt-0">Métricas agregadas</h3>
          <dl class="grid grid-cols-2 gap-y-3 gap-x-4 text-sm">
            <div>
              <dt class="text-graphite text-xs uppercase">Mejor costo</dt>
              <dd class="text-ink font-mono">{{ fmt(detalle.costo?.min) }}</dd>
            </div>
            <div>
              <dt class="text-graphite text-xs uppercase">Media ± std</dt>
              <dd class="text-ink font-mono">
                {{ fmt(detalle.costo?.media) }} ± {{ fmt(detalle.costo?.std) }}
              </dd>
            </div>
            <div>
              <dt class="text-graphite text-xs uppercase">Vehículos (media)</dt>
              <dd class="text-ink font-mono">{{ fmt(detalle.vehiculos?.media, 1) }}</dd>
            </div>
            <div>
              <dt class="text-graphite text-xs uppercase">Utilización</dt>
              <dd class="text-ink font-mono">{{ fmt(detalle.utilizacion_promedio_pct, 1) }} %</dd>
            </div>
            <div>
              <dt class="text-graphite text-xs uppercase">Tiempo medio</dt>
              <dd class="text-ink font-mono">{{ fmt(detalle.tiempo_segundos?.media, 1) }} s</dd>
            </div>
            <div v-if="detalle.demanda_total_instancia">
              <dt class="text-graphite text-xs uppercase">Demanda total</dt>
              <dd class="text-ink font-mono">{{ detalle.demanda_total_instancia }}</dd>
            </div>
          </dl>
        </div>

        <div class="card space-y-3">
          <h3 class="!mt-0">Hiperparámetros</h3>
          <pre class="text-xs bg-mist p-4 rounded overflow-x-auto"><code>{{ JSON.stringify(detalle.parametros ?? {}, null, 2) }}</code></pre>
        </div>
      </section>

      <section class="mt-12 grid md:grid-cols-2 gap-6">
        <ConvergenceChart :id="id" :titulo="detalle.nombre" />
        <RouteVisualizer :id="id" :titulo="detalle.nombre" />
      </section>

      <section v-if="detalle.mejor_run" class="mt-12 space-y-4">
        <h2>Mejor run encontrado</h2>
        <p class="text-graphite text-sm">
          Seed <code class="font-mono">{{ detalle.mejor_run.seed }}</code> ·
          generación del mejor: {{ detalle.mejor_run.generacion_mejor }} ·
          {{ detalle.mejor_run.num_vehiculos }} vehículos ·
          tiempo {{ fmt(detalle.mejor_run.tiempo_ejecucion, 1) }} s
        </p>

        <div class="card overflow-x-auto">
          <table class="w-full text-sm font-mono">
            <thead class="text-ink">
              <tr>
                <th class="text-left py-2 px-3">Vehículo</th>
                <th class="text-right py-2 px-3">Carga</th>
                <th class="text-left py-2 px-3">Ruta</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(ruta, i) in detalle.mejor_run.rutas"
                :key="i"
                class="border-t border-slate-100"
              >
                <td class="py-2 px-3 text-graphite">{{ i + 1 }}</td>
                <td class="py-2 px-3 text-right">
                  {{ detalle.mejor_run.cargas[i] }} / {{ detalle.capacidad }}
                </td>
                <td class="py-2 px-3 text-xs">{{ ruta.join(" → ") }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>

    <main class="container-prose" v-else>
      <h1>Sin datos</h1>
      <EmptyState
        titulo="No hay datos para este escenario"
        :mensaje="`No se encontró /data/${id}.json. Ejecuta make web-data después de make experiments.`"
      />
    </main>

    <AppFooter />
  </div>
</template>
