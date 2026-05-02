# Propuesta práctica: scanner propio de surebets (enfocado en tus casas)

## Objetivo
Construir una herramienta personal que:
1. recoja cuotas prematch de tus casas objetivo,
2. detecte surebets en tiempo casi real,
3. filtre por rentabilidad mínima configurable (ej. >1%),
4. te muestre solo oportunidades operables para ti.

## Enfoque recomendado (híbrido)
Según la investigación del repo, el camino más robusto es híbrido:
- **Fuente A (API agregada)** para casas con cobertura real.
- **Fuente B (adaptadores propios/scraping browser)** para casas que no estén bien cubiertas en API.

Esto evita depender de una sola plataforma y te permite controlar costos.

## Arquitectura mínima viable (MVP)

### 1) Ingesta de cuotas
- Un `collector` por proveedor/fuente.
- Cada collector produce un formato canónico:
  - `bookmaker`
  - `sport`
  - `league`
  - `event_id` (interno)
  - `home`, `away`, `start_time`
  - `market` (1X2, ML, OU, etc.)
  - `selection`
  - `odds_decimal`
  - `timestamp`

### 2) Normalización y matching
- Resolver diferencias de nombres de equipos/ligas (diccionario + fuzzy matching).
- Crear una llave de evento canónica para comparar cuotas del mismo partido en distintas casas.
- Guardar histórico corto (ej. Redis/Postgres) para detectar cambios y expiración.

### 3) Motor de surebets
Para mercado de 2 resultados:
- Hay surebet si `1/o1 + 1/o2 < 1`.

Para 3 resultados (1X2):
- Hay surebet si `1/o1 + 1/ox + 1/o2 < 1`.

ROI bruto:
- `roi = (1 - suma_inversos) * 100`.

Staking sugerido:
- Reparto proporcional a los inversos para igualar retorno bruto.

### 4) Revalidación antes de alertar
- Antes de mostrar/alertar, reconsultar cuotas de esa oportunidad en una ventana corta (2–8 s).
- Marcar estados: `fresh`, `stale`, `changed`.
- Enviar solo oportunidades `fresh`.

### 5) UI / panel
- Tabla en tiempo real con filtros:
  - casas permitidas (tus casas)
  - ROI mínimo
  - deporte/mercado
  - hora de inicio
- Botón para copiar stake recomendado.
- Semáforo de confianza (alta/media/baja) según latencia y tasa de cambio.

## Stack sugerido (vibe coding friendly)

### Opción A (rápida, flexible)
- Backend: **Python + FastAPI**
- Jobs/colas: **Celery/RQ** o scheduler simple
- DB: **PostgreSQL** (+ Redis opcional)
- Frontend: **Next.js** o **React + Vite**
- Scraping browser: **Playwright**

### Opción B (más no-code/low-code)
- Ingesta: n8n/Make para APIs fáciles
- Núcleo matemático: microservicio Python
- UI: Retool/Appsmith/Supabase Studio

## Roadmap por fases

### Fase 0 — Diseño (1–2 días)
- Definir casas exactas que usarás.
- Definir mercados iniciales (empieza por 1X2 y ML).
- Definir ROI mínimo operativo (ej. 1.5–2.5% para compensar fricción).

### Fase 1 — MVP funcional (1–2 semanas)
- 2–3 casas conectadas.
- Matching básico + cálculo surebet.
- UI simple con tabla + filtros.
- Revalidación previa a alerta.

### Fase 2 — Estabilidad (2–4 semanas)
- Logging, métricas, alertas de fallos.
- Mejorar matching de eventos.
- Control de duplicados y expiración.
- Backtesting de oportunidades detectadas vs ejecutables.

### Fase 3 — Escalado personal
- Más casas y mercados.
- Alertas Telegram/Discord.
- Priorización por “probabilidad de ejecución” y no solo ROI.

## Riesgos clave (y mitigación)
- **Latencia**: usar polling inteligente + revalidación.
- **Datos sucios/inconsistentes**: capa robusta de normalización.
- **Cambios en sitios** (si hay scraping): tests diarios de selectores y fallback.
- **Falsos positivos**: exigir estado `fresh` + TTL corto.

## Recomendaciones operativas
- No persigas solo ROI alto; prioriza oportunidades ejecutables.
- Empieza con pocos deportes/mercados y amplía después.
- Mide KPI desde el día 1:
  - oportunidades detectadas,
  - oportunidades frescas,
  - tasa de ejecución real,
  - ROI real neto.

## Plan concreto para ti (siguiente paso)
1. Me compartes lista final de casas y mercados iniciales.
2. Te devuelvo un **blueprint técnico exacto** (endpoints, esquema DB y módulos).
3. Luego pasamos a un **prompt maestro para Codex** que te genere el MVP completo por iteraciones.
