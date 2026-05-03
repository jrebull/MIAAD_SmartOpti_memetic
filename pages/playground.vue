<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

interface ProgresoEvento {
  gen: number;
  total_gen: number;
  mejor_global: number;
  mejor_gen: number;
  promedio: number;
  diversidad: number;
  mejor_cromosoma: number[];
  rutas_actuales?: number[][];
  iteraciones_tabu_acumuladas?: number;
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

interface EscenarioPreset {
  id: string;
  nombre: string;
  csv: string;
  N: number;
  capacidad: number;
  defaults: {
    generaciones: number;
    tamano_poblacion: number;
    torneo_k: number;
    prob_tabu: number;
    iter_tabu: number;
    tenencia: number;
    sample_size: number;
  };
  seeds: number[];
  tiempoEstimado: string;
  alerta?: "tibia" | "fuerte";
  notaAlerta?: string;
}

const ESCENARIOS: EscenarioPreset[] = [
  {
    id: "base_tutorial",
    nombre: "Instancia base del tutorial",
    csv: "instancia_base_25_q50.csv",
    N: 25,
    capacidad: 50,
    defaults: {
      generaciones: 50,
      tamano_poblacion: 40,
      torneo_k: 3,
      prob_tabu: 0.3,
      iter_tabu: 20,
      tenencia: 5,
      sample_size: 15,
    },
    seeds: [2026, 2027, 2028, 2029, 2030],
    tiempoEstimado: "~10 s",
  },
  {
    id: "caso_1",
    nombre: "Caso 1 — Escala Media",
    csv: "caso_1_50_clientes_q100.csv",
    N: 50,
    capacidad: 100,
    defaults: {
      generaciones: 100,
      tamano_poblacion: 60,
      torneo_k: 3,
      prob_tabu: 0.35,
      iter_tabu: 30,
      tenencia: 7,
      sample_size: 25,
    },
    seeds: [2026, 2027, 2028, 2029, 2030],
    tiempoEstimado: "~1.5–2 min",
    alerta: "tibia",
    notaAlerta: "Toma poco más de un minuto. Mantén la pestaña abierta.",
  },
  {
    id: "caso_3",
    nombre: "Caso 3 — Consolidación",
    csv: "caso_3_75_clientes_q200.csv",
    N: 75,
    capacidad: 200,
    defaults: {
      generaciones: 100,
      tamano_poblacion: 60,
      torneo_k: 3,
      prob_tabu: 0.35,
      iter_tabu: 25,
      tenencia: 7,
      sample_size: 25,
    },
    seeds: [2026, 2027, 2028, 2029, 2030],
    tiempoEstimado: "~1.5–2.5 min",
    alerta: "tibia",
    notaAlerta: "Toma cerca de dos minutos. Mantén la pestaña abierta.",
  },
  {
    id: "caso_2",
    nombre: "Caso 2 — Alta Densidad",
    csv: "caso_2_100_clientes_q30.csv",
    N: 100,
    capacidad: 30,
    defaults: {
      generaciones: 150,
      tamano_poblacion: 80,
      torneo_k: 3,
      prob_tabu: 0.45,
      iter_tabu: 35,
      tenencia: 9,
      sample_size: 35,
    },
    seeds: [2026, 2027, 2028, 2029, 2030],
    tiempoEstimado: "15–25 min",
    alerta: "fuerte",
    notaAlerta:
      "Este escenario es muy pesado en el navegador (Pyodide es ~3-5× más lento que Python nativo). Te recomiendo ver los resultados precalculados en /escenarios/caso_2.",
  },
];

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
  "caso_1_50_clientes_q100.csv",
  "caso_2_100_clientes_q30.csv",
  "caso_3_75_clientes_q200.csv",
  "runner.py",
];

const estado = ref<"cargando" | "lista" | "corriendo" | "terminada" | "error">("cargando");
const mensaje = ref("Cargando Pyodide y NumPy (~10 MB la primera vez)…");
const progresoCarga = ref(0);
const progreso = ref<ProgresoEvento | null>(null);
const historicoVivo = ref<number[]>([]);
const resultado = ref<ResultadoFinal | null>(null);
const errorMsg = ref("");
const nodosBase = ref<Nodo[]>([]);

const escenarioSeleccionado = ref<string>("base_tutorial");
const escenarioActual = computed<EscenarioPreset>(
  () => ESCENARIOS.find((e) => e.id === escenarioSeleccionado.value) ?? ESCENARIOS[0]
);

// Hiperparámetros (sliders).
const seed = ref(2026);
const generaciones = ref(50);
const tamano_poblacion = ref(40);
const torneo_k = ref(3);
const prob_tabu = ref(0.3);
const iter_tabu = ref(20);
const tenencia = ref(5);
const sample_size = ref(15);

function aplicarDefaults(preset: EscenarioPreset) {
  generaciones.value = preset.defaults.generaciones;
  tamano_poblacion.value = preset.defaults.tamano_poblacion;
  torneo_k.value = preset.defaults.torneo_k;
  prob_tabu.value = preset.defaults.prob_tabu;
  iter_tabu.value = preset.defaults.iter_tabu;
  tenencia.value = preset.defaults.tenencia;
  sample_size.value = preset.defaults.sample_size;
}

watch(escenarioSeleccionado, async (nuevoId) => {
  const preset = ESCENARIOS.find((e) => e.id === nuevoId);
  if (preset) {
    aplicarDefaults(preset);
    await cargarNodosDelEscenario(preset.csv);
  }
});

let pyodide: any = null;
let cancelarBucle = false;

async function cargarArchivoEnFS(py: any, ruta: string): Promise<void> {
  const url = `/playground/${ruta}`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`fetch ${url} → ${r.status}`);
  const contenido = await r.text();
  const destino = `/playground/${ruta}`;
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

async function cargarNodosDelEscenario(csv: string) {
  try {
    const r = await fetch(`/playground/${csv}`);
    if (!r.ok) return;
    const texto = await r.text();
    const lineas = texto.trim().split("\n").slice(1);
    nodosBase.value = lineas.map((l) => {
      const [id, x, y, demanda] = l.split(",").map(Number);
      return { id, x, y, demanda };
    });
  } catch {
    /* ignorar */
  }
}

async function inicializarPyodide(): Promise<void> {
  try {
    if (!(window as any).loadPyodide) {
      await new Promise<void>((resolve, reject) => {
        const s = document.createElement("script");
        s.src = `${PYODIDE_CDN}pyodide.js`;
        s.onload = () => resolve();
        s.onerror = () => reject(new Error("No se pudo cargar Pyodide"));
        document.head.appendChild(s);
      });
    }
    progresoCarga.value = 25;
    mensaje.value = "Inicializando intérprete Python…";
    pyodide = await (window as any).loadPyodide({ indexURL: PYODIDE_CDN });
    progresoCarga.value = 55;
    mensaje.value = "Cargando NumPy…";
    await pyodide.loadPackage(["numpy"]);
    progresoCarga.value = 80;
    mensaje.value = "Montando paquete y 4 instancias…";
    for (let i = 0; i < ARCHIVOS_PY.length; i++) {
      await cargarArchivoEnFS(pyodide, ARCHIVOS_PY[i]);
      progresoCarga.value = 80 + Math.floor(((i + 1) / ARCHIVOS_PY.length) * 20);
    }
    pyodide.runPython("import sys\nsys.path.insert(0, '/playground')\nimport runner");

    await cargarNodosDelEscenario(escenarioActual.value.csv);

    estado.value = "lista";
    mensaje.value = "Listo. Elige escenario, ajusta parámetros y dale 'Correr'.";
    progresoCarga.value = 100;
  } catch (e: any) {
    estado.value = "error";
    errorMsg.value = String(e?.message ?? e);
  }
}

async function correr(): Promise<void> {
  if (estado.value === "corriendo") {
    cancelarBucle = true;
    return;
  }
  cancelarBucle = false;
  estado.value = "corriendo";
  resultado.value = null;
  progreso.value = null;
  historicoVivo.value = [];
  const preset = escenarioActual.value;
  mensaje.value = `Inicializando ${preset.nombre}…`;

  await new Promise((r) => setTimeout(r, 30));

  try {
    pyodide.globals.set("ui_seed", seed.value);
    pyodide.globals.set("ui_generaciones", generaciones.value);
    pyodide.globals.set("ui_tamano_poblacion", tamano_poblacion.value);
    pyodide.globals.set("ui_torneo_k", torneo_k.value);
    pyodide.globals.set("ui_prob_tabu", prob_tabu.value);
    pyodide.globals.set("ui_iter_tabu", iter_tabu.value);
    pyodide.globals.set("ui_tenencia", tenencia.value);
    pyodide.globals.set("ui_sample_size", sample_size.value);
    pyodide.globals.set("ui_instancia_csv", preset.csv);
    pyodide.globals.set("ui_capacidad", preset.capacidad);

    const initCode = `
runner.iniciar_run(
    seed=int(ui_seed),
    generaciones=int(ui_generaciones),
    tamano_poblacion=int(ui_tamano_poblacion),
    torneo_k=int(ui_torneo_k),
    prob_tabu=float(ui_prob_tabu),
    iter_tabu=int(ui_iter_tabu),
    tenencia=int(ui_tenencia),
    sample_size=int(ui_sample_size),
    instancia_csv=str(ui_instancia_csv),
    capacidad=int(ui_capacidad),
)
`;
    const initJson = await pyodide.runPythonAsync(initCode);
    const init = JSON.parse(initJson) as ProgresoEvento;
    progreso.value = init;
    historicoVivo.value = [init.mejor_global];
    mensaje.value = `Generación 0/${generaciones.value} — empezando…`;

    for (let g = 1; g <= generaciones.value; g++) {
      if (cancelarBucle) {
        mensaje.value = `Cancelado en generación ${g - 1}/${generaciones.value}.`;
        break;
      }
      const evJson = await pyodide.runPythonAsync(`runner.paso()`);
      const ev = JSON.parse(evJson) as ProgresoEvento;
      progreso.value = ev;
      historicoVivo.value.push(ev.mejor_global);
      mensaje.value = `Gen ${g}/${generaciones.value} · mejor ${ev.mejor_global.toFixed(2)} · diversidad ${(ev.diversidad * 100).toFixed(0)}%`;
      await new Promise((r) => setTimeout(r, 0));
    }

    const finalJson = await pyodide.runPythonAsync(`runner.finalizar()`);
    const datos = JSON.parse(finalJson) as ResultadoFinal;
    resultado.value = datos;
    estado.value = "terminada";
    mensaje.value = `Terminado en ${datos.tiempo_segundos.toFixed(2)} s · costo ${datos.costo_final.toFixed(2)} · ${datos.num_vehiculos} vehículos.`;
  } catch (e: any) {
    estado.value = "error";
    errorMsg.value = String(e?.message ?? e);
  } finally {
    cancelarBucle = false;
  }
}

const pathConvergencia = computed<string>(() => {
  const datos = resultado.value
    ? resultado.value.historico_convergencia
    : historicoVivo.value;
  if (datos.length < 2) return "";
  const minY = Math.min(...datos);
  const maxY = Math.max(...datos);
  const rango = maxY - minY || 1;
  const W = 600;
  const H = 220;
  const N = Math.max(2, Math.max(generaciones.value, datos.length));
  return datos
    .map((y, i) => {
      const px = (i / (N - 1)) * (W - 20) + 10;
      const py = H - 20 - ((y - minY) / rango) * (H - 40);
      return `${i === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)}`;
    })
    .join(" ");
});

const rutasParaDibujar = computed(() => {
  const rutas = resultado.value
    ? resultado.value.rutas
    : progreso.value?.rutas_actuales || [];
  const nodos = resultado.value ? resultado.value.nodos : nodosBase.value;
  const mapa = new Map(nodos.map((n) => [n.id, n]));
  const paleta = ["#5A72A0", "#83B4FF", "#3D5A80", "#FF7F50", "#2E8B57", "#8B5A8C", "#B6CCE0", "#C792EA"];
  return rutas
    .filter((r) => r.length >= 2)
    .map((ruta, k) => ({
      color: paleta[k % paleta.length],
      puntos: ruta
        .map((cid) => mapa.get(cid))
        .filter((n): n is Nodo => Boolean(n))
        .map((n) => ({ x: n.x, y: n.y })),
    }));
});

const minMaxConv = computed(() => {
  const datos = resultado.value
    ? resultado.value.historico_convergencia
    : historicoVivo.value;
  if (!datos.length) return { min: 0, max: 0 };
  return { min: Math.min(...datos), max: Math.max(...datos) };
});

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
        <p class="text-graphite text-lg">
          El paquete <code>memetico_cvrp</code> ejecutándose <strong>dentro de tu navegador</strong>
          vía Pyodide / WebAssembly. Elige uno de los 4 escenarios, ajusta los hiperparámetros
          y observa la convergencia generación por generación.
        </p>
      </header>

      <!-- Selector de escenario -->
      <section class="mt-8">
        <p class="text-xs uppercase tracking-wider text-graphite mb-3">Escenario</p>
        <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <button
            v-for="e in ESCENARIOS"
            :key="e.id"
            @click="escenarioSeleccionado = e.id"
            :class="[
              'text-left p-3 rounded-lg border transition-all',
              escenarioSeleccionado === e.id
                ? 'border-ink bg-ink text-white shadow-sm'
                : 'border-slate-200 bg-white hover:border-graphite hover:bg-slate-50',
            ]"
          >
            <p :class="['text-sm font-semibold', escenarioSeleccionado === e.id ? 'text-white' : 'text-ink']">
              {{ e.nombre }}
            </p>
            <p :class="['text-xs font-mono mt-1', escenarioSeleccionado === e.id ? 'text-slate-200' : 'text-graphite']">
              N={{ e.N }} · Q={{ e.capacidad }}
            </p>
            <p :class="['text-xs mt-2', escenarioSeleccionado === e.id ? 'text-slate-300' : 'text-graphite']">
              ⏱ {{ e.tiempoEstimado }}
            </p>
          </button>
        </div>

        <div
          v-if="escenarioActual.alerta"
          :class="[
            'mt-4 p-3 rounded-lg border text-sm',
            escenarioActual.alerta === 'fuerte'
              ? 'border-amber-300 bg-amber-50 text-amber-900'
              : 'border-sky/40 bg-sky/10 text-ink',
          ]"
        >
          <strong>{{ escenarioActual.alerta === "fuerte" ? "Atención:" : "Nota:" }}</strong>
          {{ escenarioActual.notaAlerta }}
          <span v-if="escenarioActual.alerta === 'fuerte'">
            <NuxtLink :to="`/escenarios/${escenarioActual.id}`" class="underline">Ir a /escenarios/{{ escenarioActual.id }}</NuxtLink>.
          </span>
        </div>
      </section>

      <!-- Estado / progreso de carga -->
      <section class="mt-6">
        <div
          :class="[
            'card text-sm transition-all',
            estado === 'error' ? 'border-red-300 bg-red-50' : 'border-slate-100',
          ]"
        >
          <div class="flex items-center gap-3">
            <span
              v-if="estado === 'cargando' || estado === 'corriendo'"
              class="inline-block h-3 w-3 rounded-full bg-graphite animate-pulse"
            />
            <span v-else-if="estado === 'lista'" class="inline-block h-3 w-3 rounded-full bg-emerald-500" />
            <span v-else-if="estado === 'terminada'" class="inline-block h-3 w-3 rounded-full bg-sky" />
            <span v-else class="inline-block h-3 w-3 rounded-full bg-red-500" />
            <span class="text-ink">{{ mensaje }}</span>
          </div>
          <div v-if="estado === 'cargando'" class="mt-3 h-2 w-full bg-slate-100 rounded overflow-hidden">
            <div class="h-full bg-graphite transition-all duration-300" :style="{ width: `${progresoCarga}%` }" />
          </div>
          <div v-if="progreso && estado === 'corriendo'" class="mt-3 h-2 w-full bg-slate-100 rounded overflow-hidden">
            <div
              class="h-full bg-sky transition-all duration-150"
              :style="{ width: `${(progreso.gen / progreso.total_gen) * 100}%` }"
            />
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

      <section class="mt-6 flex items-center gap-3 flex-wrap">
        <button
          @click="correr"
          :disabled="estado === 'cargando' || estado === 'error'"
          :class="[
            'px-5 py-2 rounded text-sm font-medium transition-all',
            estado === 'corriendo'
              ? 'bg-red-600 text-white hover:bg-red-700'
              : 'bg-ink text-white hover:bg-graphite',
            'disabled:bg-slate-300 disabled:cursor-not-allowed',
          ]"
        >
          {{ estado === "corriendo" ? "Cancelar" : `Correr ${escenarioActual.nombre}` }}
        </button>
        <span v-if="progreso" class="text-xs text-graphite font-mono">
          mejor global: {{ progreso.mejor_global.toFixed(2) }} ·
          diversidad: {{ (progreso.diversidad * 100).toFixed(0) }}% ·
          gen: {{ progreso.gen }}/{{ progreso.total_gen }}
        </span>
      </section>

      <!-- Vivo: convergencia + rutas en paralelo -->
      <section v-if="progreso || resultado" class="mt-10 grid md:grid-cols-2 gap-6">
        <div class="card">
          <h3 class="!mt-0 flex items-baseline justify-between">
            <span>Convergencia</span>
            <span class="text-xs text-graphite font-mono">
              {{ minMaxConv.min.toFixed(0) }} – {{ minMaxConv.max.toFixed(0) }}
            </span>
          </h3>
          <svg viewBox="0 0 600 220" class="w-full h-auto mt-2">
            <line x1="10" :y1="200" x2="590" :y2="200" stroke="#E2E8F0" stroke-width="0.5" />
            <line x1="10" :y1="20" x2="10" :y2="200" stroke="#E2E8F0" stroke-width="0.5" />
            <path :d="pathConvergencia" fill="none" stroke="#1A2130" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <p class="text-xs text-graphite mt-2 font-mono">Mejor global por generación</p>
        </div>

        <div class="card">
          <h3 class="!mt-0 flex items-baseline justify-between">
            <span>Mapa de rutas</span>
            <span v-if="rutasParaDibujar.length" class="text-xs text-graphite font-mono">
              {{ rutasParaDibujar.length }} vehíc.
            </span>
          </h3>
          <svg viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet" class="w-full h-auto bg-mist rounded mt-2">
            <g
              v-for="(r, i) in rutasParaDibujar"
              :key="i"
              :stroke="r.color"
              stroke-width="0.45"
              fill="none"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <polyline :points="r.puntos.map((p) => `${p.x},${100 - p.y}`).join(' ')" />
              <circle
                v-for="(p, j) in r.puntos.slice(1, -1)"
                :key="j"
                :cx="p.x"
                :cy="100 - p.y"
                r="0.9"
                :fill="r.color"
              />
            </g>
            <polygon points="50,46.5 53.5,53.5 46.5,53.5" fill="#1A2130" />
          </svg>
          <p class="text-xs text-graphite mt-2 font-mono text-center">
            Triángulo: depósito · cada color es una ruta de un vehículo
          </p>
        </div>
      </section>

      <!-- Resultado final -->
      <section v-if="resultado" class="mt-10 space-y-4">
        <h2>Resultado final</h2>
        <div class="grid md:grid-cols-4 gap-4">
          <div class="card">
            <p class="text-xs uppercase text-graphite tracking-wide">Costo final</p>
            <p class="text-2xl font-mono text-ink mt-1">{{ resultado.costo_final.toFixed(2) }}</p>
          </div>
          <div class="card">
            <p class="text-xs uppercase text-graphite tracking-wide">Vehículos</p>
            <p class="text-2xl font-mono text-ink mt-1">{{ resultado.num_vehiculos }}</p>
          </div>
          <div class="card">
            <p class="text-xs uppercase text-graphite tracking-wide">Utilización</p>
            <p class="text-2xl font-mono text-ink mt-1">{{ resultado.utilizacion_pct.toFixed(1) }} %</p>
          </div>
          <div class="card">
            <p class="text-xs uppercase text-graphite tracking-wide">Tiempo</p>
            <p class="text-2xl font-mono text-ink mt-1">{{ resultado.tiempo_segundos.toFixed(2) }} s</p>
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
              <tr v-for="(ruta, i) in resultado.rutas" :key="i" class="border-t border-slate-100">
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
          del repo</em>: lo ves en <NuxtLink to="/codigo">/código</NuxtLink>.
        </p>
        <p>
          La animación en vivo funciona porque cada generación se ejecuta como un
          paso atómico desde JS (<code>runner.paso()</code>) cediendo el event loop
          entre llamadas. Los 4 CSVs de las instancias se montan en el filesystem
          virtual de Pyodide al cargar, así que cambiar de escenario no requiere
          recargar nada.
        </p>
      </section>
    </main>

    <AppFooter />
  </div>
</template>
