<script setup lang="ts">
const links = [
  { to: "/", label: "Inicio" },
  { to: "/escenarios", label: "Escenarios" },
  { to: "/playground", label: "Playground" },
  { to: "/metodologia", label: "Metodología" },
  { to: "/about", label: "Acerca" },
];
</script>

<template>
  <header class="bg-white border-b border-slate-100 sticky top-0 z-30 backdrop-blur">
    <nav class="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
      <NuxtLink to="/" class="font-serif text-lg font-semibold text-ink no-underline">
        Memético <span class="text-graphite font-normal">· CVRP</span>
      </NuxtLink>
      <ul class="flex gap-6 text-sm">
        <li v-for="l in links" :key="l.to">
          <NuxtLink
            :to="l.to"
            class="text-graphite hover:text-ink no-underline transition-colors"
            active-class="text-ink font-semibold"
          >
            {{ l.label }}
          </NuxtLink>
        </li>
      </ul>
    </nav>
  </header>
</template>
