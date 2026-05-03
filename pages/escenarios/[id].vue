<script setup lang="ts">
import { computed } from "vue";

import caso_1 from "~/assets/data/caso_1.json";
import caso_2 from "~/assets/data/caso_2.json";
import caso_3 from "~/assets/data/caso_3.json";

interface Nodo {
  id: number;
  x: number;
  y: number;
  demanda: number;
}

const route = useRoute();
const id = String(route.params.id);

const detalleMap: Record<string, unknown> = { caso_1, caso_2, caso_3 };
const detalle = detalleMap[id] as any;

function fmt(x?: number, dec = 2): string {
  if (x === undefined || x === null || isNaN(x as number)) return "—";
  return Number(x).toFixed(dec);
}

// Paleta consistente con plots.py / playground.
const PALETA = [
  "#5A72A0", "#83B4FF", "#3D5A80", "#FF7F50",
  "#2E8B57", "#8B5A8C", "#B6CCE0", "#C792EA",
  "#1A2130", "#6B8E23",
];

interface VehiculoVista {
  index: number;
  ruta: number[];
  carga: number;
  capacidad: number;
  utilizacion: number;
  numClientes: number;
  distancia: number;
  color: string;
  puntos: { id: number; x: number; y: number }[];
}

const nodosMap = computed(() => {
  if (!detalle?.nodos) return new Map<number, Nodo>();
  return new Map<number, Nodo>(
    detalle.nodos.map((n: Nodo) => [n.id, n])
  );
});

function distanciaRuta(ruta: number[]): number {
  const m = nodosMap.value;
  let d = 0;
  for (let i = 0; i < ruta.length - 1; i++) {
    const a = m.get(ruta[i]);
    const b = m.get(ruta[i + 1]);
    if (!a || !b) continue;
    d += Math.hypot(a.x - b.x, a.y - b.y);
  }
  return d;
}

const vehiculos = computed<VehiculoVista[]>(() => {
  if (!detalle?.mejor_run) return [];
  const r: number[][] = detalle.mejor_run.rutas;
  const c: number[] = detalle.mejor_run.cargas;
  const cap: number = detalle.capacidad;
  const m = nodosMap.value;
  return r.map((ruta, i) => {
    const puntos = ruta
      .map((cid) => m.get(cid))
      .filter((n): n is Nodo => Boolean(n))
      .map((n) => ({ id: n.id, x: n.x, y: n.y }));
    return {
      index: i + 1,
      ruta,
      carga: c[i],
      capacidad: cap,
      utilizacion: (c[i] / cap) * 100,
      numClientes: ruta.length - 2,
      distancia: distanciaRuta(ruta),
      color: PALETA[i % PALETA.length],
      puntos,
    };
  });
});

// Para el mini-mapa: contexto global (todos los nodos en gris claro)
// + ruta del vehículo en color.
const todosLosClientes = computed(() => {
  if (!detalle?.nodos) return [];
  return detalle.nodos.filter((n: Nodo) => n.id !== 0);
});

function pathDe(puntos: { x: number; y: number }[]): string {
  if (puntos.length < 2) return "";
  return puntos
    .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(2)},${(100 - p.y).toFixed(2)}`)
    .join(" ");
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
          <span class="pill">N = {{ todosLosClientes.length }}</span>
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
              <dd class="text-ink font-mono">{{ fmt(detalle.costo?.media) }} ± {{ fmt(detalle.costo?.std) }}</dd>
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

      <!-- ============ MEJOR RUN ENCONTRADO ============ -->
      <section v-if="detalle.mejor_run" class="mt-16 space-y-6">
        <header class="flex items-baseline justify-between flex-wrap gap-3">
          <h2 class="!mt-0 !mb-0">Mejor run encontrado</h2>
          <span class="text-xs text-graphite font-mono">
            seed {{ detalle.mejor_run.seed }}
          </span>
        </header>

        <!-- Stats grandes del mejor run -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-px bg-slate-200 rounded-xl overflow-hidden border border-slate-200">
          <div class="bg-white px-5 py-4">
            <p class="text-[10px] uppercase tracking-wider text-graphite">Costo final</p>
            <p class="text-2xl font-mono font-bold text-ink mt-1">{{ fmt(detalle.mejor_run.costo_final) }}</p>
          </div>
          <div class="bg-white px-5 py-4">
            <p class="text-[10px] uppercase tracking-wider text-graphite">Vehículos</p>
            <p class="text-2xl font-mono font-bold text-ink mt-1">{{ detalle.mejor_run.num_vehiculos }}</p>
          </div>
          <div class="bg-white px-5 py-4">
            <p class="text-[10px] uppercase tracking-wider text-graphite">Gen. del mejor</p>
            <p class="text-2xl font-mono font-bold text-ink mt-1">{{ detalle.mejor_run.generacion_mejor }}</p>
          </div>
          <div class="bg-white px-5 py-4">
            <p class="text-[10px] uppercase tracking-wider text-graphite">Tiempo</p>
            <p class="text-2xl font-mono font-bold text-ink mt-1">{{ fmt(detalle.mejor_run.tiempo_ejecucion, 1) }} s</p>
          </div>
        </div>

        <!-- Grid de tarjetas por vehículo -->
        <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <article
            v-for="v in vehiculos"
            :key="v.index"
            class="bg-white rounded-xl border border-slate-200 overflow-hidden hover:border-ink hover:shadow-md transition-all"
          >
            <!-- Header -->
            <div class="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <span class="inline-block w-3 h-3 rounded-full" :style="{ backgroundColor: v.color }" />
                <span class="font-semibold text-ink">Vehículo {{ v.index }}</span>
              </div>
              <span class="text-xs font-mono text-graphite">
                {{ v.numClientes }} clientes · {{ v.distancia.toFixed(1) }} u
              </span>
            </div>

            <!-- Mini-mapa con contexto -->
            <div class="bg-mist border-b border-slate-100 p-3">
              <svg viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet" class="w-full h-32">
                <!-- Todos los clientes en gris muy sutil -->
                <circle
                  v-for="n in todosLosClientes"
                  :key="`bg-${n.id}`"
                  :cx="n.x"
                  :cy="100 - n.y"
                  r="0.6"
                  fill="#CBD5E1"
                  opacity="0.5"
                />
                <!-- Path de la ruta -->
                <path
                  :d="pathDe(v.puntos)"
                  fill="none"
                  :stroke="v.color"
                  stroke-width="0.8"
                  stroke-linejoin="round"
                  stroke-linecap="round"
                />
                <!-- Clientes de esta ruta resaltados -->
                <circle
                  v-for="(p, j) in v.puntos.slice(1, -1)"
                  :key="`r-${j}`"
                  :cx="p.x"
                  :cy="100 - p.y"
                  r="1.4"
                  :fill="v.color"
                  stroke="white"
                  stroke-width="0.4"
                />
                <!-- Depósito -->
                <polygon points="50,46.5 53.5,53.5 46.5,53.5" fill="#1A2130" />
              </svg>
            </div>

            <!-- Barra de utilización + métrica -->
            <div class="px-4 py-3 space-y-2">
              <div class="flex items-baseline justify-between text-xs">
                <span class="text-graphite uppercase tracking-wider">Carga</span>
                <span class="font-mono text-ink">
                  <strong>{{ v.carga }}</strong> / {{ v.capacidad }}
                  <span class="text-graphite">({{ v.utilizacion.toFixed(0) }}%)</span>
                </span>
              </div>
              <div class="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all"
                  :style="{
                    width: `${v.utilizacion}%`,
                    backgroundColor: v.color,
                  }"
                />
              </div>
            </div>

            <!-- Secuencia compacta -->
            <div class="px-4 py-3 border-t border-slate-100 bg-slate-50/60">
              <p class="text-[10px] uppercase tracking-wider text-graphite mb-1.5">Secuencia</p>
              <p class="font-mono text-xs text-ink leading-relaxed break-all">
                <span
                  v-for="(c, k) in v.ruta"
                  :key="k"
                  :class="c === 0 ? 'text-graphite' : ''"
                >
                  {{ c }}<span v-if="k < v.ruta.length - 1" class="text-slate-300"> → </span>
                </span>
              </p>
            </div>
          </article>
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
