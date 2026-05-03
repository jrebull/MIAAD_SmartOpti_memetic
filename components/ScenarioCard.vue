<script setup lang="ts">
interface Escenario {
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
}

const props = defineProps<{ escenario: Escenario }>();

function fmt(x?: number, dec = 2): string {
  if (x === undefined || x === null || isNaN(x as number)) return "—";
  return Number(x).toFixed(dec);
}
</script>

<template>
  <NuxtLink :to="`/escenarios/${escenario.id}`" class="no-underline group">
    <div class="card hover:border-graphite hover:-translate-y-0.5 hover:shadow-md transition-all space-y-4">
      <header class="flex items-baseline justify-between">
        <h3 class="!mt-0 !mb-0 group-hover:text-ink">{{ escenario.nombre }}</h3>
        <span class="pill">{{ escenario.id }}</span>
      </header>

      <dl class="grid grid-cols-2 gap-y-3 gap-x-4 text-sm">
        <div>
          <dt class="text-graphite text-xs uppercase tracking-wide">Mejor costo</dt>
          <dd class="text-ink font-mono text-lg">{{ fmt(escenario.costo_mejor) }}</dd>
        </div>
        <div>
          <dt class="text-graphite text-xs uppercase tracking-wide">Media ± std</dt>
          <dd class="text-ink font-mono text-lg">
            {{ fmt(escenario.costo_media) }}
            <span class="text-graphite text-sm">± {{ fmt(escenario.costo_std) }}</span>
          </dd>
        </div>
        <div>
          <dt class="text-graphite text-xs uppercase tracking-wide">Vehículos</dt>
          <dd class="text-ink font-mono text-lg">{{ escenario.vehiculos_mejor ?? "—" }}</dd>
        </div>
        <div>
          <dt class="text-graphite text-xs uppercase tracking-wide">Utilización</dt>
          <dd class="text-ink font-mono text-lg">{{ fmt(escenario.utilizacion_pct, 1) }}%</dd>
        </div>
      </dl>

      <p class="text-xs text-graphite">
        Tiempo medio: {{ fmt(escenario.tiempo_media_s, 1) }} s · {{ escenario.n_runs ?? 0 }} runs
      </p>
    </div>
  </NuxtLink>
</template>
