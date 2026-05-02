<template>
  <div>
    <AppHeader />
    <main class="container-prose">
      <h1>Acerca</h1>

      <section class="space-y-3">
        <p>
          Trabajo final de la materia <strong>Optimización Inteligente</strong>
          (impartida por el Mtro. Raúl Gibrán Porras Alaniz) de la
          <strong>Maestría en Inteligencia Artificial y Analítica de Datos
          (MIAAD)</strong> de la <strong>Universidad Autónoma de Ciudad
          Juárez (UACJ)</strong>.
        </p>
        <p>
          Autor: <strong>Javier Augusto Rebull Saucedo</strong> (matrícula 263483).
          Entrega: mayo de 2026.
        </p>
      </section>

      <h2>Reglas autoimpuestas</h2>
      <ul>
        <li>Implementación desde cero, sin librerías de optimización VRP externas.</li>
        <li>Reproducibilidad bit a bit: dos runs con la misma seed → resultados idénticos.</li>
        <li>Cada métrica reportada se regenera desde los archivos de resultados; cero métricas hardcodeadas.</li>
        <li>El reporte LaTeX se compila en Overleaf, no localmente.</li>
      </ul>

      <h2>Recursos</h2>
      <ul>
        <li>
          Código y reporte:
          <a href="https://github.com/jrebull/MIAAD_SmartOpti_memetic" target="_blank" rel="noopener">
            jrebull/MIAAD_SmartOpti_memetic
          </a>
        </li>
        <li>Documentación de reproducibilidad: <code>docs/REPRODUCIBILITY.md</code></li>
        <li>Decisiones arquitectónicas: <code>docs/adr/</code></li>
      </ul>
    </main>
    <AppFooter />
  </div>
</template>
