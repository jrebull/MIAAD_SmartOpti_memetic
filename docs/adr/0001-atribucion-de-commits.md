# ADR 0001 — Atribución de commits

**Fecha:** 2026-05-02
**Estado:** Aceptado

## Contexto

El plan brutal (`Prompts/PLAN_BRUTAL_USER_STORIES_MEMETICO_CVRP.md`) no especifica si los commits deben llevar `Co-Authored-By: Claude`. El proyecto previo del mismo alumno (`/Users/haowei/Documents/MIAAD/SMART/EstrategiasEvolutivas/CLAUDE.md`) sí lo especifica explícitamente:

> Commits firmados solo como `Javier Rebull <rebull@outlook.com>`. Sin `Co-Authored-By: Claude` (trabajo académico).

## Decisión

Todos los commits se firman únicamente como `Javier Rebull <rebull@outlook.com>`. **No** se añade `Co-Authored-By: Claude` ni ninguna línea que delate generación asistida.

Razones:
1. Es trabajo académico evaluado por un profesor. La atribución única refleja la autoría de la entrega.
2. Mantiene consistencia con el proyecto previo del mismo programa.
3. Las herramientas usadas (Claude Code, copilots) son comparables a usar un IDE: no se acreditan por convención.

## Consecuencias

- Comandos de commit usan `-c user.email=rebull@outlook.com` para forzar el email correcto sin modificar el `git config --global`.
- El cuerpo del mensaje no menciona Claude, IA ni ningún copiloto.
- Si en algún momento el alumno decide cambiar la atribución, se actualiza este ADR y se documenta la nueva política.
