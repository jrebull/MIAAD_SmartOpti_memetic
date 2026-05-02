<script setup lang="ts">
defineProps<{ id: string; titulo: string; alt?: string }>();
</script>

<template>
  <figure class="card overflow-hidden">
    <img
      :src="`/images/rutas_${id}.png`"
      :alt="alt ?? `Mapa de rutas del escenario ${titulo}`"
      class="w-full h-auto rounded-md"
      loading="lazy"
    />
    <figcaption class="text-xs text-graphite mt-3 text-center">
      Mapa de rutas — {{ titulo }}
    </figcaption>
  </figure>
</template>
