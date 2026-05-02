<script setup lang="ts">
interface Fila {
  id: string;
  nombre: string;
  costo_mejor?: number;
  costo_media?: number;
  costo_std?: number;
  vehiculos_media?: number;
  utilizacion_pct?: number;
  tiempo_media_s?: number;
}

defineProps<{ filas: Fila[] }>();

function fmt(x?: number, dec = 2): string {
  if (x === undefined || x === null || isNaN(x as number)) return "—";
  return Number(x).toFixed(dec);
}
</script>

<template>
  <div class="overflow-x-auto card !p-0">
    <table class="w-full text-sm">
      <thead class="bg-mist text-ink">
        <tr>
          <th class="text-left py-3 px-4 font-semibold">Escenario</th>
          <th class="text-right py-3 px-4 font-semibold">Mejor</th>
          <th class="text-right py-3 px-4 font-semibold">Media</th>
          <th class="text-right py-3 px-4 font-semibold">Std</th>
          <th class="text-right py-3 px-4 font-semibold">Vehíc.</th>
          <th class="text-right py-3 px-4 font-semibold">Útil. %</th>
          <th class="text-right py-3 px-4 font-semibold">Tiempo s</th>
        </tr>
      </thead>
      <tbody class="font-mono">
        <tr
          v-for="f in filas"
          :key="f.id"
          class="border-t border-slate-100 hover:bg-mist/60 transition-colors"
        >
          <td class="py-3 px-4 text-ink">{{ f.nombre }}</td>
          <td class="py-3 px-4 text-right">{{ fmt(f.costo_mejor) }}</td>
          <td class="py-3 px-4 text-right">{{ fmt(f.costo_media) }}</td>
          <td class="py-3 px-4 text-right">{{ fmt(f.costo_std) }}</td>
          <td class="py-3 px-4 text-right">{{ fmt(f.vehiculos_media, 1) }}</td>
          <td class="py-3 px-4 text-right">{{ fmt(f.utilizacion_pct, 1) }}</td>
          <td class="py-3 px-4 text-right">{{ fmt(f.tiempo_media_s, 1) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
