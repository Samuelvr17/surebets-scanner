# Surebets Scanner (MVP local)

Arquitectura de persistencia orientada a arrancar solo, sin operar servidores.

## Decisión técnica: SQLite local + repositorios Python

Se usa **SQLite** como base única local porque:

- No requiere desplegar ni administrar servidores.
- Soporta transacciones ACID y constraints (evita corrupción y duplicados).
- Escala bien para un MVP de captura prematch en una sola máquina.
- Facilita migrar más adelante a Postgres (mismo modelo relacional).

La inicialización de tablas e índices vive en `src/storage/database.py` y los accesos en `src/storage/repositories.py`.

---

## 1) Modelo de captura cruda (`raw_odds_captures`)

Objetivo: guardar exactamente lo recibido por cada casa como “caja negra”.

Campos clave:

- `bookmaker`: casa de apuestas origen.
- `source_event_id`: id del evento tal como viene del proveedor.
- `fetched_at_utc`: instante de captura en UTC.
- `payload_json`: respuesta original serializada.
- `payload_hash`: hash para deduplicar capturas repetidas.
- `collector_version`: versión del colector que tomó la captura.
- `UNIQUE(bookmaker, payload_hash)`: evita almacenar el mismo payload dos veces.

Uso: auditoría, debugging y reproducibilidad de normalización/matching.

---

## 2) Modelo de cuota normalizada (`normalized_odds`)

Objetivo: transformar distintas fuentes a un formato unificado comparable.

Campos clave:

- `capture_id`: referencia a la captura cruda origen.
- `canonical_event_key`: clave canónica del partido (misma clave para BetPlay/RushBet).
- `sport`, `league`, `home_team`, `away_team`, `event_start_utc`.
- `market_type`, `selection`, `line_value`, `odds_decimal`.
- Índice por `canonical_event_key + market_type + normalized_at_utc` para comparación eficiente.

Esto permite que variantes como:
- “Atl. Nacional vs Millonarios”
- “Nacional Medellín - Millonarios FC”

terminen en la **misma representación canónica** antes de arbitrar.

---

## 3) Modelo de surebet detectada (`surebet_opportunities`)

Objetivo: mantener historial de oportunidades detectadas y su ciclo de vida.

Campos clave:

- `opportunity_key`: id único de oportunidad (evita duplicados).
- `canonical_event_key`, `market_type`.
- `implied_probability_sum`, `expected_roi_percent`.
- `legs_json`: detalle de piernas (bookmaker, selección, cuota).
- `stake_plan_json`: distribución sugerida de stake.
- `detected_at_utc`, `validated_at_utc`, `expires_at_utc`.
- `status`: `detected | validated | expired | executed | rejected`.

Con esto puedes distinguir oportunidades reales de falsos positivos o expiradas.

---

## Flujo recomendado de persistencia

1. **Captura**: guardar `raw_odds_captures` con deduplicación por hash.
2. **Normalización**: generar una o varias filas `normalized_odds` por captura.
3. **Matching/Arbitraje**: detectar surebets y persistir en `surebet_opportunities`.
4. **Validación**: actualizar `status` según comprobación/ejecución.

---

## Evolución futura sin reescribir todo

Cuando el volumen crezca:

- Mantener el contrato de repositorios y migrar de SQLite a Postgres.
- Agregar particionado temporal para captura cruda.
- Añadir jobs de retención (ej. conservar payload crudo 30-90 días).

