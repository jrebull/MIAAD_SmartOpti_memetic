<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";

// Imports estáticos: Vite los inlinea como string en build time.
import dataPy from "~/assets/codigo/data.py?raw";
import distancePy from "~/assets/codigo/distance.py?raw";
import splitPy from "~/assets/codigo/split.py?raw";
import geneticPy from "~/assets/codigo/genetic.py?raw";
import tabuPy from "~/assets/codigo/tabu.py?raw";
import memeticPy from "~/assets/codigo/memetic.py?raw";
import feasibilityPy from "~/assets/codigo/feasibility.py?raw";

interface Modulo {
  id: string;
  nombre: string;
  rol: string;
  descripcion: string;
  conceptos: string[];
  codigo: string;
  loc: number;
}

const MODULOS: Modulo[] = [
  {
    id: "data",
    nombre: "data.py",
    rol: "Generación y carga de instancias CVRP",
    descripcion:
      "Define los tipos `Nodo` e `Instancia`, genera instancias deterministas (mismo seed → mismo CSV byte-a-byte) y las carga validando estructura, depósito, demanda total y capacidad.",
    conceptos: ["dataclass frozen", "random.Random(seed)", "MD5 + .meta.json", "validación de invariantes"],
    codigo: dataPy,
    loc: dataPy.split("\n").length,
  },
  {
    id: "distance",
    nombre: "distance.py",
    rol: "Matriz de distancias euclidianas",
    descripcion:
      "Precomputa la matriz `(N+1)×(N+1)` de distancias euclidianas vectorizada con NumPy (`np.hypot` + broadcasting) — convierte cada acceso a distancia en O(1) y evita recomputar Pitágoras millones de veces.",
    conceptos: ["np.hypot", "broadcasting", "matriz simétrica", "float64"],
    codigo: distancePy,
    loc: distancePy.split("\n").length,
  },
  {
    id: "split",
    nombre: "split.py",
    rol: "Decodificador Giant Tour → rutas factibles",
    descripcion:
      "Recorre el cromosoma (permutación de clientes) de izquierda a derecha y abre una nueva ruta cuando la siguiente demanda excedería la capacidad. Devuelve `(costo, rutas, cargas)`. Toda permutación válida es una solución factible.",
    conceptos: ["Split capacitado", "validación: duplicados/faltantes/rango", "ResultadoSplit dataclass"],
    codigo: splitPy,
    loc: splitPy.split("\n").length,
  },
  {
    id: "genetic",
    nombre: "genetic.py",
    rol: "Operadores genéticos (población, torneo, OX)",
    descripcion:
      "Tres operadores fundamentales del Algoritmo Genético: muestreo de población inicial diversa, selección por torneo de tamaño k, y Order Crossover (OX) que preserva la invariante de permutación al cruzar.",
    conceptos: ["np.random.Generator inyectado", "torneo k", "Order Crossover (Davis 1985)", "wrap-around"],
    codigo: geneticPy,
    loc: geneticPy.split("\n").length,
  },
  {
    id: "tabu",
    nombre: "tabu.py",
    rol: "Búsqueda Tabú (intensificación local)",
    descripcion:
      "Búsqueda local con memoria: opera por swaps de dos clientes, mantiene una lista tabú con tenencia configurable, aplica criterio de aspiración y acepta el mejor vecino del muestreo aunque empeore — esto fuerza la salida de óptimos locales.",
    conceptos: ["swap neighborhood", "lista tabú normalizada", "tenencia", "aspiración", "muestreo de vecinos"],
    codigo: tabuPy,
    loc: tabuPy.split("\n").length,
  },
  {
    id: "memetic",
    nombre: "memetic.py",
    rol: "Orquestador GA + Tabú + elitismo",
    descripcion:
      "El director: evoluciona la población con GA (selección + OX) y, con probabilidad p_tabu, somete cada hijo a una corrida corta de Tabú para 'educarlo'. Mantiene caché de fitness, elitismo del campeón previo y emite eventos por generación vía callback opcional.",
    conceptos: ["ConfigMemetico (frozen)", "elitismo", "caché de fitness", "callback on_generation"],
    codigo: memeticPy,
    loc: memeticPy.split("\n").length,
  },
  {
    id: "feasibility",
    nombre: "feasibility.py",
    rol: "Validador blindado de soluciones",
    descripcion:
      "Cierre de seguridad: valida que toda solución reportada inicia/termina en depósito, cubre cada cliente exactamente una vez, no excede capacidad y que el costo recalculado coincide dentro de tolerancia. Si algo falla, levanta `SolucionInvalidaError` con mensaje detallado.",
    conceptos: ["3 restricciones duras CVRP", "cross-check de costo", "SolucionInvalidaError"],
    codigo: feasibilityPy,
    loc: feasibilityPy.split("\n").length,
  },
];

const seleccionado = ref<string>("data");
const moduloActual = computed(() => MODULOS.find((m) => m.id === seleccionado.value)!);
const totalLOC = computed(() => MODULOS.reduce((s, m) => s + m.loc, 0));

const codigoEl = ref<HTMLElement | null>(null);

async function aplicarHighlight() {
  if (typeof window === "undefined") return;
  const win = window as any;
  if (!win.hljs) {
    // Cargar highlight.js desde CDN solo en cliente (no afecta SSG / bundle).
    await new Promise<void>((resolve, reject) => {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = "https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.10.0/build/styles/atom-one-light.min.css";
      document.head.appendChild(link);

      const s = document.createElement("script");
      s.src = "https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.10.0/build/highlight.min.js";
      s.onload = () => resolve();
      s.onerror = () => reject();
      document.head.appendChild(s);
    });
  }
  await nextTick();
  if (codigoEl.value && win.hljs) {
    codigoEl.value.removeAttribute("data-highlighted");
    win.hljs.highlightElement(codigoEl.value);
  }
}

watch(seleccionado, () => aplicarHighlight());
onMounted(() => aplicarHighlight());
</script>

<template>
  <div>
    <AppHeader />

    <main class="max-w-6xl mx-auto px-6 md:px-8 py-12">
      <header class="space-y-3 max-w-3xl">
        <span class="pill">Código fuente · Python</span>
        <h1>El paquete <code class="font-mono text-3xl">memetico_cvrp</code></h1>
        <p class="text-graphite text-lg">
          Siete módulos. {{ totalLOC }} líneas de Python sin librerías VRP externas.
          Cada pieza es independiente, testeable y reutilizable. El mismo código
          que corre en
          <NuxtLink to="/playground">Playground</NuxtLink> dentro de tu navegador.
        </p>
      </header>

      <div class="mt-10 grid md:grid-cols-[260px_1fr] gap-6">
        <!-- Sidebar: módulos -->
        <aside class="space-y-1.5 md:sticky md:top-20 md:self-start">
          <button
            v-for="m in MODULOS"
            :key="m.id"
            @click="seleccionado = m.id"
            :class="[
              'w-full text-left p-3 rounded border transition-all',
              seleccionado === m.id
                ? 'border-ink bg-ink text-white shadow-sm'
                : 'border-slate-200 bg-white text-ink hover:border-graphite hover:bg-slate-50',
            ]"
          >
            <div class="font-mono text-sm flex items-baseline justify-between">
              <span>{{ m.nombre }}</span>
              <span :class="seleccionado === m.id ? 'text-sky/70' : 'text-graphite'" class="text-xs">{{ m.loc }} LOC</span>
            </div>
            <div :class="seleccionado === m.id ? 'text-slate-200' : 'text-graphite'" class="text-xs mt-1">
              {{ m.rol }}
            </div>
          </button>
        </aside>

        <!-- Visor -->
        <article class="space-y-6">
          <div class="card">
            <h2 class="!mt-0 !mb-2 font-mono">{{ moduloActual.nombre }}</h2>
            <p class="text-graphite text-sm font-medium">{{ moduloActual.rol }}</p>
            <p class="mt-3 text-ink leading-relaxed">{{ moduloActual.descripcion }}</p>
            <div class="mt-4 flex flex-wrap gap-1.5">
              <span v-for="c in moduloActual.conceptos" :key="c" class="pill">{{ c }}</span>
            </div>
          </div>

          <div class="rounded-lg overflow-hidden border border-slate-200 bg-slate-50">
            <div class="px-4 py-2 bg-slate-100 border-b border-slate-200 flex items-center justify-between">
              <span class="font-mono text-xs text-graphite">src/memetico_cvrp/{{ moduloActual.nombre }}</span>
              <span class="text-xs text-graphite">{{ moduloActual.loc }} líneas</span>
            </div>
            <pre class="m-0 overflow-x-auto !bg-slate-50 text-sm leading-relaxed"><code ref="codigoEl" class="language-python !bg-transparent !p-4">{{ moduloActual.codigo }}</code></pre>
          </div>

          <p class="text-xs text-graphite">
            Repo:
            <a
              :href="`https://github.com/jrebull/MIAAD_SmartOpti_memetic/blob/main/src/memetico_cvrp/${moduloActual.nombre}`"
              target="_blank"
              rel="noopener"
            >
              github.com/jrebull/MIAAD_SmartOpti_memetic
            </a>
          </p>
        </article>
      </div>
    </main>

    <AppFooter />
  </div>
</template>
