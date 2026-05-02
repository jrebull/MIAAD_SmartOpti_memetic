<script setup lang="ts">
defineProps<{ id: string; titulo: string; alt?: string }>();
</script>

<template>
  <figure class="card overflow-hidden">
    <img
      :src="`/images/convergencia_${id}.png`"
      :alt="alt ?? `Curva de convergencia del escenario ${titulo}`"
      class="w-full h-auto rounded-md"
      loading="lazy"
    />
    <figcaption class="text-xs text-graphite mt-3 text-center">
      Convergencia (mejor global por generación) — {{ titulo }}
    </figcaption>
  </figure>
</template>
