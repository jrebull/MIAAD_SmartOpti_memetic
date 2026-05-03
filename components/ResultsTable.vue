<script setup lang="ts">
import { computed } from "vue";

interface Fila {
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

const props = defineProps<{ filas: Fila[] }>();

function fmt(x?: number, dec = 2): string {
  if (x === undefined || x === null || isNaN(x as number)) return "—";
  return Number(x).toFixed(dec);
}

function fmtTiempo(s?: number): string {
  if (!s || isNaN(s)) return "—";
  if (s < 60) return `${s.toFixed(1)} s`;
  return `${(s / 60).toFixed(1)} min`;
}

const PALETA_BARRA = ["#5A72A0", "#83B4FF", "#3D5A80", "#2E8B57", "#FF7F50", "#8B5A8C"];

const maxCosto = computed(() =>
  Math.max(...props.filas.map((f) => f.costo_mejor ?? 0), 1)
);
const maxVehic = computed(() =>
  Math.max(...props.filas.map((f) => f.vehiculos_mejor ?? 0), 1)
);
const minCosto = computed(() =>
  Math.min(...props.filas.map((f) => f.costo_mejor ?? Infinity))
);
</script>

<template>
  <div class="space-y-3">
    <article
      v-for="(f, i) in filas"
      :key="f.id"
      class="bg-white rounded-xl border border-slate-200 p-5 hover:border-ink hover:shadow-md transition-all"
    >
      <!-- Header de la fila -->
      <header class="flex items-baseline justify-between flex-wrap gap-2 mb-4">
        <div class="flex items-baseline gap-3">
          <span
            class="inline-block w-3 h-3 rounded-full"
            :style="{ backgroundColor: PALETA_BARRA[i % PALETA_BARRA.length] }"
          />
          <h3 class="!mt-0 !mb-0 text-lg font-semibold text-ink font-sans">
            {{ f.nombre }}
          </h3>
          <span class="pill">{{ f.id }}</span>
        </div>
        <span class="text-xs text-graphite font-mono">
          n = {{ f.n_runs ?? 0 }} runs
        </span>
      </header>

      <!-- Stat principal: costo con barra proporcional -->
      <div class="space-y-1.5">
        <div class="flex items-baseline justify-between text-xs">
          <span class="uppercase tracking-wider text-graphite">Mejor costo</span>
          <span
            v-if="f.costo_mejor === minCosto"
            class="text-emerald-700 font-semibold"
          >
            ★ mínimo del lote
          </span>
        </div>
        <div class="flex items-baseline gap-3">
          <span class="text-2xl font-mono font-bold text-ink">{{ fmt(f.costo_mejor) }}</span>
          <span class="text-xs text-graphite font-mono">
            media {{ fmt(f.costo_media) }} ± {{ fmt(f.costo_std) }}
          </span>
        </div>
        <div class="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
          <div
            class="h-full rounded-full transition-all"
            :style="{
              width: `${((f.costo_mejor ?? 0) / maxCosto) * 100}%`,
              backgroundColor: PALETA_BARRA[i % PALETA_BARRA.length],
            }"
          />
        </div>
      </div>

      <!-- Métricas secundarias -->
      <div class="mt-5 grid grid-cols-3 gap-4 pt-4 border-t border-slate-100">
        <!-- Vehículos -->
        <div>
          <p class="text-[10px] uppercase tracking-wider text-graphite">Vehículos</p>
          <div class="mt-1 flex items-baseline gap-1.5">
            <span class="text-lg font-mono font-semibold text-ink">{{ f.vehiculos_mejor ?? "—" }}</span>
            <span class="text-[10px] text-graphite">de {{ maxVehic }} max</span>
          </div>
          <div class="mt-1.5 h-1 w-full bg-slate-100 rounded-full overflow-hidden">
            <div
              class="h-full bg-graphite rounded-full"
              :style="{ width: `${((f.vehiculos_mejor ?? 0) / maxVehic) * 100}%` }"
            />
          </div>
        </div>

        <!-- Utilización -->
        <div>
          <p class="text-[10px] uppercase tracking-wider text-graphite">Utilización</p>
          <div class="mt-1 flex items-baseline gap-1.5">
            <span class="text-lg font-mono font-semibold text-ink">{{ fmt(f.utilizacion_pct, 1) }}%</span>
          </div>
          <div class="mt-1.5 h-1 w-full bg-slate-100 rounded-full overflow-hidden">
            <div
              class="h-full bg-emerald-500 rounded-full"
              :style="{ width: `${f.utilizacion_pct ?? 0}%` }"
            />
          </div>
        </div>

        <!-- Tiempo -->
        <div>
          <p class="text-[10px] uppercase tracking-wider text-graphite">Tiempo medio</p>
          <div class="mt-1 flex items-baseline gap-1.5">
            <span class="text-lg font-mono font-semibold text-ink">{{ fmtTiempo(f.tiempo_media_s) }}</span>
          </div>
          <div class="mt-1.5 h-1 w-full bg-slate-100 rounded-full overflow-hidden">
            <div
              class="h-full bg-sky rounded-full"
              :style="{
                width: `${Math.min(100, ((f.tiempo_media_s ?? 0) / 320) * 100)}%`,
              }"
            />
          </div>
        </div>
      </div>
    </article>
  </div>
</template>
