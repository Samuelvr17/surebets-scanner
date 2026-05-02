# Surebets Scanner (MVP local)

## Captura de cuotas: base browser-first con contrato homogéneo

Se implementó un **colector base** para las 5 casas (`betplay`, `rushbet`, `stake_colombia`, `codere_colombia`, `sportium_colombia`) con estas garantías:

- Todas reciben la misma configuración (`CollectorRuntimeConfig` + `BookmakerCollectorConfig`).
- Todas devuelven el mismo formato intermedio (`CollectorResult` + `CaptureRecord`).
- Todas guardan dump crudo JSON en `data/raw_captures/<bookmaker>/...`.
- Si una casa falla, falla de forma controlada y no detiene las demás.

## Placeholders para tu captura manual (F12 / XHR)

Tal como definiste, el input real vendrá de tu trabajo manual en navegador.

Por cada casa debes completar:

- `<BOOKMAKER>_XHR_URL`
- `<BOOKMAKER>_JSON_SAMPLE`

Mientras no se completen, el colector reporta error controlado (esperado).

## Guardar sesión manual reutilizable

Comando:

```bash
python -m src.main --save-session betplay
```

Repite cambiando casa (`rushbet`, `stake_colombia`, `codere_colombia`, `sportium_colombia`).

Esto abre Chromium visible (Playwright), tú inicias sesión manualmente una sola vez y se guarda el estado en:

- `data/sessions/<bookmaker>_state.json`

## Ejecutar captura

```bash
python -m src.main
```

Devuelve resumen JSON por casa con capturas y errores.
