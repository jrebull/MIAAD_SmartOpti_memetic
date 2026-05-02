<script setup lang="ts">
defineProps<{ titulo?: string; mensaje?: string }>();
</script>

<template>
  <div class="card text-center py-12">
    <p class="text-lg text-ink font-semibold mb-2">
      {{ titulo ?? "Sin resultados aún" }}
    </p>
    <p class="text-graphite text-sm max-w-md mx-auto">
      {{
        mensaje ??
        "Corre `make experiments && make web-data` para generar los resultados y ver esta sección poblada."
      }}
    </p>
  </div>
</template>
