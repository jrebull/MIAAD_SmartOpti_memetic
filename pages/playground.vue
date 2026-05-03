<script setup lang="ts">
import { onMounted, ref } from "vue";

interface ProgresoEvento {
  gen: number;
  total_gen: number;
  mejor_global: number;
  mejor_gen: number;
  promedio: number;
  diversidad: number;
  mejor_cromosoma: number[];
}

interface Nodo {
  id: number;
  x: number;
  y: number;
  demanda: number;
}

interface ResultadoFinal {
  ok: boolean;
  tiempo_segundos: number;
  costo_final: number;
  num_vehiculos: number;
  utilizacion_pct: number;
  generacion_mejor: number;
  iteraciones_tabu_aplicadas: number;
  aceptaciones_no_mejorantes_tabu: number;
  historico_convergencia: number[];
  historico_promedio: number[];
  rutas: number[][];
  cargas: number[];
  mejor_cromosoma: number[];
  configuracion: Record<string, number>;
  nodos: Nodo[];
}

const PYODIDE_VERSION = "0.26.4";
const PYODIDE_CDN = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
const ARCHIVOS_PY = [
  "memetico_cvrp/__init__.py",
  "memetico_cvrp/data.py",
  "memetico_cvrp/distance.py",
  "memetico_cvrp/split.py",
  "memetico_cvrp/genetic.py",
  "memetico_cvrp/tabu.py",
  "memetico_cvrp/memetic.py",
  "memetico_cvrp/feasibility.py",
  "instancia_base_25_q50.csv",
  "runner.py",
];

const estado = ref<"cargando" | "lista" | "corriendo" | "terminada" | "error">("cargando");
const mensaje = ref("Cargando Pyodide y NumPy (~10 MB la primera vez)…");
const progreso = ref<ProgresoEvento | null>(null);
const resultado = ref<ResultadoFinal | null>(null);
const errorMsg = ref("");

// Hiperparámetros (sliders).
const seed = ref(2026);
const generaciones = ref(50);
const tamano_poblacion = ref(40);
const torneo_k = ref(3);
const prob_tabu = ref(0.3);
const iter_tabu = ref(20);
const tenencia = ref(5);
const sample_size = ref(15);

let pyodide: any = null;

async function cargarArchivoEnFS(py: any, ruta: string): Promise<void> {
  const url = `/playground/${ruta}`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`fetch ${url} → ${r.status}`);
  const contenido = await r.text();
  const destino = `/playground/${ruta}`;
  // Crear directorios padre si faltan.
  const partes = destino.split("/").slice(1, -1);
  let acumulado = "";
  for (const p of partes) {
    acumulado += `/${p}`;
    try {
      py.FS.mkdir(acumulado);
    } catch {
      /* ya existe */
    }
  }
  py.FS.writeFile(destino, contenido);
}

async function inicializarPyodide(): Promise<void> {
  try {
    // Carga el script de Pyodide desde CDN.
    if (!(window as any).loadPyodide) {
      await new Promise<void>((resolve, reject) => {
        const s = document.createElement("script");
        s.src = `${PYODIDE_CDN}pyodide.js`;
        s.onload = () => resolve();
        s.onerror = () => reject(new Error("No se pudo cargar Pyodide"));
        document.head.appendChild(s);
      });
    }
    mensaje.value = "Inicializando intérprete Python…";
    pyodide = await (window as any).loadPyodide({ indexURL: PYODIDE_CDN });
    mensaje.value = "Cargando NumPy…";
    await pyodide.loadPackage(["numpy"]);
    mensaje.value = "Montando paquete memetico_cvrp…";
    for (const archivo of ARCHIVOS_PY) {
      await cargarArchivoEnFS(pyodide, archivo);
    }
    // Importar el runner.
    pyodide.runPython("import sys\nsys.path.insert(0, '/playground')\nimport runner");
    estado.value = "lista";
    mensaje.value = "Listo. Ajusta los parámetros y dale 'Correr'.";
  } catch (e: any) {
    estado.value = "error";
    errorMsg.value = String(e?.message ?? e);
  }
}

function animarConvergencia(historico: number[]): void {
  // Reproduce el histórico generación a generación (~50 ms cada una)
  // para que el usuario vea la curva crecer aunque el cómputo haya sido bloqueante.
  if (!historico.length) return;
  const total = historico.length;
  const intervalo = Math.max(15, Math.min(80, Math.floor(2500 / total)));
  let i = 1;
  progreso.value = {
    gen: 0,
    total_gen: total - 1,
    mejor_global: historico[0],
    mejor_gen: historico[0],
    promedio: historico[0],
    diversidad: 1.0,
    mejor_cromosoma: [],
  };
  const id = setInterval(() => {
    if (i >= total) {
      clearInterval(id);
      return;
    }
    progreso.value = {
      gen: i,
      total_gen: total - 1,
      mejor_global: historico[i],
      mejor_gen: historico[i],
      promedio: historico[i],
      diversidad: 1.0,
      mejor_cromosoma: [],
    };
    i++;
  }, intervalo);
}

async function correr(): Promise<void> {
  if (estado.value !== "lista" && estado.value !== "terminada") return;
  estado.value = "corriendo";
  resultado.value = null;
  progreso.value = null;
  mensaje.value = "Procesando — Pyodide está corriendo Python en este navegador. No cierres la pestaña (~5–60 s según parámetros).";

  // Cede el hilo para que la UI redibuje el "Corriendo" antes de bloquear.
  await new Promise((r) => setTimeout(r, 30));

  try {
    // Inyecta los parámetros como globales Python y ejecuta vía runPythonAsync.
    // Este patrón evita problemas de binding al llamar callKwargs sobre un PyProxy.
    pyodide.globals.set("ui_seed", seed.value);
    pyodide.globals.set("ui_generaciones", generaciones.value);
    pyodide.globals.set("ui_tamano_poblacion", tamano_poblacion.value);
    pyodide.globals.set("ui_torneo_k", torneo_k.value);
    pyodide.globals.set("ui_prob_tabu", prob_tabu.value);
    pyodide.globals.set("ui_iter_tabu", iter_tabu.value);
    pyodide.globals.set("ui_tenencia", tenencia.value);
    pyodide.globals.set("ui_sample_size", sample_size.value);

    const code = `
runner.correr_playground(
    seed=int(ui_seed),
    generaciones=int(ui_generaciones),
    tamano_poblacion=int(ui_tamano_poblacion),
    torneo_k=int(ui_torneo_k),
    prob_tabu=float(ui_prob_tabu),
    iter_tabu=int(ui_iter_tabu),
    tenencia=int(ui_tenencia),
    sample_size=int(ui_sample_size),
)
`;
    const jsonResultado: string = await pyodide.runPythonAsync(code);
    const datos = JSON.parse(jsonResultado) as ResultadoFinal;
    resultado.value = datos;
    estado.value = "terminada";
    mensaje.value = `Terminado en ${datos.tiempo_segundos.toFixed(2)} s.`;
    // Animación retro de la convergencia.
    animarConvergencia(datos.historico_convergencia);
  } catch (e: any) {
    estado.value = "error";
    errorMsg.value = String(e?.message ?? e);
  }
}

function pathConvergencia(): string {
  // SVG path de la curva de convergencia (mejor global).
  const datos = resultado.value
    ? resultado.value.historico_convergencia
    : progreso.value
      ? Array.from({ length: progreso.value.gen + 1 }, () => progreso.value!.mejor_global)
      : [];
  if (datos.length < 2) return "";
  const minY = Math.min(...datos);
  const maxY = Math.max(...datos);
  const rango = maxY - minY || 1;
  const W = 600;
  const H = 220;
  return datos
    .map((y, i) => {
      const px = (i / (datos.length - 1)) * (W - 20) + 10;
      const py = H - 20 - ((y - minY) / rango) * (H - 40);
      return `${i === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)}`;
    })
    .join(" ");
}

function vistaRutas(): { rutas: { color: string; puntos: { x: number; y: number }[] }[] } {
  if (!resultado.value || !resultado.value.nodos.length) return { rutas: [] };
  const nodos = new Map(resultado.value.nodos.map((n) => [n.id, n]));
  const paleta = ["#5A72A0", "#83B4FF", "#3D5A80", "#FF7F50", "#2E8B57", "#8B5A8C", "#B6CCE0"];
  const rutas = resultado.value.rutas.map((ruta, k) => ({
    color: paleta[k % paleta.length],
    puntos: ruta.map((cid) => {
      const n = nodos.get(cid)!;
      return { x: n.x, y: n.y };
    }),
  }));
  return { rutas };
}

onMounted(() => {
  inicializarPyodide();
});
</script>

<template>
  <div>
    <AppHeader />

    <main class="container-prose">
      <header class="space-y-3">
        <span class="pill">Demo interactiva · Pyodide</span>
        <h1>Playground</h1>
        <p class="text-graphite">
          El mismo código Python del paquete <code>memetico_cvrp</code> corriendo
          dentro de tu navegador (vía Pyodide / WebAssembly). Ajusta los hiperparámetros
          y observa la convergencia generación por generación sobre la instancia base
          de <strong>25 clientes</strong> (Q = 50).
        </p>
      </header>

      <!-- Estado y mensajes -->
      <section class="mt-6">
        <div
          :class="[
            'card text-sm',
            estado === 'error' ? 'border-red-300 bg-red-50' : 'border-slate-100',
          ]"
        >
          <div class="flex items-center gap-3">
            <span
              v-if="estado === 'cargando' || estado === 'corriendo'"
              class="inline-block h-3 w-3 rounded-full bg-graphite animate-pulse"
            />
            <span
              v-else-if="estado === 'lista'"
              class="inline-block h-3 w-3 rounded-full bg-emerald-500"
            />
            <span
              v-else-if="estado === 'terminada'"
              class="inline-block h-3 w-3 rounded-full bg-sky"
            />
            <span
              v-else
              class="inline-block h-3 w-3 rounded-full bg-red-500"
            />
            <span class="text-ink">{{ mensaje }}</span>
          </div>
          <p v-if="errorMsg" class="mt-3 text-red-700 text-xs font-mono whitespace-pre-wrap">
            {{ errorMsg }}
          </p>
        </div>
      </section>

      <!-- Sliders -->
      <section class="mt-8 grid md:grid-cols-2 gap-x-8 gap-y-5">
        <label class="space-y-1">
          <div class="flex justify-between text-sm">
            <span class="text-graphite">Semilla (seed)</span>
            <span class="font-mono text-ink">{{ seed }}</span>
          </div>
          <input v-model.number="seed" type="number" class="w-full px-3 py-1 border border-slate-200 rounded text-sm font-mono" />
        </label>

        <label class="space-y-1">
          <div class="flex justify-between text-sm">
            <span class="text-graphite">Generaciones</span>
            <span class="font-mono text-ink">{{ generaciones }}</span>
          </div>
          <input v-model.number="generaciones" type="range" min="10" max="200" step="5" class="w-full" />
        </label>

        <label class="space-y-1">
          <div class="flex justify-between text-sm">
            <span class="text-graphite">Tamaño de población (μ)</span>
            <span class="font-mono text-ink">{{ tamano_poblacion }}</span>
          </div>
          <input v-model.number="tamano_poblacion" type="range" min="10" max="100" step="5" class="w-full" />
        </label>

        <label class="space-y-1">
          <div class="flex justify-between text-sm">
            <span class="text-graphite">Torneo k</span>
            <span class="font-mono text-ink">{{ torneo_k }}</span>
          </div>
          <input v-model.number="torneo_k" type="range" min="2" max="7" step="1" class="w-full" />
        </label>

        <label class="space-y-1">
          <div class="flex justify-between text-sm">
            <span class="text-graphite">Probabilidad de Tabú</span>
            <span class="font-mono text-ink">{{ prob_tabu.toFixed(2) }}</span>
          </div>
          <input v-model.number="prob_tabu" type="range" min="0" max="1" step="0.05" class="w-full" />
        </label>

        <label class="space-y-1">
          <div class="flex justify-between text-sm">
            <span class="text-graphite">Iteraciones Tabú por hijo</span>
            <span class="font-mono text-ink">{{ iter_tabu }}</span>
          </div>
          <input v-model.number="iter_tabu" type="range" min="5" max="50" step="5" class="w-full" />
        </label>

        <label class="space-y-1">
          <div class="flex justify-between text-sm">
            <span class="text-graphite">Tenencia Tabú</span>
            <span class="font-mono text-ink">{{ tenencia }}</span>
          </div>
          <input v-model.number="tenencia" type="range" min="2" max="15" step="1" class="w-full" />
        </label>

        <label class="space-y-1">
          <div class="flex justify-between text-sm">
            <span class="text-graphite">Vecinos por iteración (sample)</span>
            <span class="font-mono text-ink">{{ sample_size }}</span>
          </div>
          <input v-model.number="sample_size" type="range" min="5" max="40" step="5" class="w-full" />
        </label>
      </section>

      <section class="mt-6 flex items-center gap-3">
        <button
          @click="correr"
          :disabled="estado !== 'lista' && estado !== 'terminada'"
          class="px-5 py-2 bg-ink text-white rounded text-sm font-medium hover:bg-graphite disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
        >
          {{ estado === "corriendo" ? "Corriendo…" : "Correr memético" }}
        </button>
        <p v-if="progreso && estado === 'corriendo'" class="text-xs text-graphite font-mono">
          Gen {{ progreso.gen }}/{{ progreso.total_gen }} · mejor global
          {{ progreso.mejor_global.toFixed(2) }} · diversidad
          {{ (progreso.diversidad * 100).toFixed(0) }}%
        </p>
      </section>

      <!-- Convergencia en vivo -->
      <section v-if="progreso || resultado" class="mt-10 space-y-3">
        <h2>Convergencia</h2>
        <div class="card !p-3">
          <svg viewBox="0 0 600 220" class="w-full h-auto">
            <path
              :d="pathConvergencia()"
              fill="none"
              stroke="#1A2130"
              stroke-width="2"
            />
          </svg>
          <p class="text-xs text-graphite mt-2 font-mono">
            Mejor global por generación
          </p>
        </div>
      </section>

      <!-- Mapa de rutas -->
      <section v-if="resultado" class="mt-10 space-y-3">
        <h2>Solución</h2>
        <div class="grid md:grid-cols-3 gap-4">
          <div class="card md:col-span-1 space-y-3">
            <h3 class="!mt-0">Métricas</h3>
            <dl class="grid grid-cols-2 gap-y-2 text-sm">
              <dt class="text-graphite">Costo final</dt>
              <dd class="font-mono text-ink">{{ resultado.costo_final.toFixed(2) }}</dd>
              <dt class="text-graphite">Vehículos</dt>
              <dd class="font-mono text-ink">{{ resultado.num_vehiculos }}</dd>
              <dt class="text-graphite">Utilización</dt>
              <dd class="font-mono text-ink">{{ resultado.utilizacion_pct.toFixed(1) }} %</dd>
              <dt class="text-graphite">Gen. del mejor</dt>
              <dd class="font-mono text-ink">{{ resultado.generacion_mejor }}</dd>
              <dt class="text-graphite">Tiempo</dt>
              <dd class="font-mono text-ink">{{ resultado.tiempo_segundos.toFixed(2) }} s</dd>
              <dt class="text-graphite">Iter. Tabú</dt>
              <dd class="font-mono text-ink">{{ resultado.iteraciones_tabu_aplicadas }}</dd>
              <dt class="text-graphite">No-mejorantes</dt>
              <dd class="font-mono text-ink">{{ resultado.aceptaciones_no_mejorantes_tabu }}</dd>
            </dl>
          </div>

          <div class="card md:col-span-2">
            <svg viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet" class="w-full h-auto bg-mist rounded">
              <g v-for="(r, i) in vistaRutas().rutas" :key="i" :stroke="r.color" stroke-width="0.4" fill="none">
                <polyline
                  :points="r.puntos.map((p) => `${p.x},${100 - p.y}`).join(' ')"
                />
                <circle
                  v-for="(p, j) in r.puntos.slice(1, -1)"
                  :key="j"
                  :cx="p.x"
                  :cy="100 - p.y"
                  r="0.9"
                  :fill="r.color"
                />
              </g>
              <!-- Depósito -->
              <polygon points="50,47 53,53 47,53" fill="#1A2130" />
            </svg>
            <p class="text-xs text-graphite mt-2 font-mono text-center">
              Triángulo: depósito · cada color es una ruta de un vehículo
            </p>
          </div>
        </div>

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
                v-for="(ruta, i) in resultado.rutas"
                :key="i"
                class="border-t border-slate-100"
              >
                <td class="py-2 px-3 text-graphite">{{ i + 1 }}</td>
                <td class="py-2 px-3 text-right">
                  {{ resultado.cargas[i] }} / {{ resultado.configuracion.capacidad }}
                </td>
                <td class="py-2 px-3 text-xs">{{ ruta.join(" → ") }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="mt-12 text-xs text-graphite space-y-2">
        <p>
          <strong>Notas técnicas.</strong> Pyodide v{{ PYODIDE_VERSION }} carga el
          intérprete Python + NumPy en el navegador (~10 MB la primera vez, en caché
          después). El paquete <code>memetico_cvrp</code> es <em>el mismo código Python
          del repo</em>, no una reimplementación: se sincroniza con
          <code>scripts/preparar_playground.py</code>.
        </p>
        <p>
          La instancia base es la del tutorial (seed = 2026, N = 25, Q = 50). Los
          tres escenarios oficiales (50/100/75 clientes) no se ejecutan aquí porque
          tomarían entre 30 s y 5 min en el navegador del visitante; sus resultados
          precalculados están en
          <NuxtLink to="/escenarios">/escenarios</NuxtLink>.
        </p>
      </section>
    </main>

    <AppFooter />
  </div>
</template>
