<script setup lang="ts">
const año = new Date().getFullYear();
</script>

<template>
  <footer class="border-t border-slate-100 mt-24 bg-white">
    <div class="max-w-5xl mx-auto px-6 py-10 text-sm text-graphite flex flex-col md:flex-row justify-between gap-4">
      <div>
        <p class="font-medium text-ink">
          Algoritmo Memético CVRP — MIAAD UACJ · Mayo {{ año }}
        </p>
        <p class="mt-1">Javier Augusto Rebull Saucedo · Matrícula 263483</p>
      </div>
      <div class="space-y-1">
        <p>
          <a
            href="https://github.com/jrebull/MIAAD_SmartOpti_memetic"
            target="_blank"
            rel="noopener"
            class="text-graphite hover:text-ink"
          >
            GitHub
          </a>
        </p>
        <p>
          Materia: Optimización Inteligente — Mtro. Raúl Gibrán Porras Alaniz
        </p>
      </div>
    </div>
  </footer>
</template>
