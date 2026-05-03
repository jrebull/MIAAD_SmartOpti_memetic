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

function fmtTiempo(s?: number): string {
  if (!s || isNaN(s)) return "—";
  if (s < 60) return `${s.toFixed(0)} s`;
  return `${(s / 60).toFixed(1)} min`;
}
</script>

<template>
  <NuxtLink
    :to="`/escenarios/${escenario.id}`"
    class="no-underline group block h-full"
  >
    <article
      class="h-full flex flex-col bg-white rounded-xl border border-slate-200 overflow-hidden hover:border-ink hover:shadow-lg hover:-translate-y-0.5 transition-all"
    >
      <!-- Preview del mapa de rutas como banner superior -->
      <div class="relative h-36 bg-mist overflow-hidden border-b border-slate-100">
        <img
          :src="`/images/rutas_${escenario.id}.png`"
          :alt="`Vista previa de rutas — ${escenario.nombre}`"
          loading="lazy"
          class="absolute inset-0 w-full h-full object-cover object-center opacity-70 group-hover:opacity-90 group-hover:scale-105 transition-all duration-500"
        />
        <span class="absolute top-3 left-3 pill bg-white/90 backdrop-blur-sm">
          {{ escenario.id }}
        </span>
        <span class="absolute top-3 right-3 inline-flex items-center justify-center w-7 h-7 rounded-full bg-ink text-white opacity-0 group-hover:opacity-100 transition-opacity text-sm">
          →
        </span>
      </div>

      <!-- Cuerpo -->
      <div class="flex-1 p-5 space-y-4">
        <h3 class="!mt-0 !mb-0 text-lg font-sans font-semibold text-ink leading-tight">
          {{ escenario.nombre }}
        </h3>

        <!-- Stat principal: mejor costo -->
        <div>
          <p class="text-[10px] uppercase tracking-wider text-graphite font-medium">
            Mejor costo (n={{ escenario.n_runs ?? 0 }} runs)
          </p>
          <p class="mt-1 text-3xl font-mono font-bold text-ink leading-none">
            {{ fmt(escenario.costo_mejor) }}
          </p>
          <p class="mt-1 text-xs text-graphite font-mono">
            media {{ fmt(escenario.costo_media) }} ± {{ fmt(escenario.costo_std) }}
          </p>
        </div>

        <!-- Stats secundarios: grid 3 cols compacto -->
        <div class="grid grid-cols-3 gap-2 pt-3 border-t border-slate-100">
          <div>
            <p class="text-[10px] uppercase tracking-wider text-graphite">Vehículos</p>
            <p class="text-base font-mono font-semibold text-ink mt-0.5">
              {{ escenario.vehiculos_mejor ?? "—" }}
            </p>
          </div>
          <div>
            <p class="text-[10px] uppercase tracking-wider text-graphite">Utilización</p>
            <p class="text-base font-mono font-semibold text-ink mt-0.5">
              {{ fmt(escenario.utilizacion_pct, 1) }}%
            </p>
          </div>
          <div>
            <p class="text-[10px] uppercase tracking-wider text-graphite">Tiempo</p>
            <p class="text-base font-mono font-semibold text-ink mt-0.5">
              {{ fmtTiempo(escenario.tiempo_media_s) }}
            </p>
          </div>
        </div>
      </div>
    </article>
  </NuxtLink>
</template>
