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

## Depurar un colector individual (tiempo real)

```bash
python -m src.collectors.debug_tools betplay --show-files
```

Opciones útiles:
- `--show-files`: muestra tamaño/ubicación exacta de cada dump crudo guardado.
- `--show-payload`: imprime el payload completo capturado.

El resumen final incluye:
- duración real,
- número de capturas,
- duplicados descartados,
- lista exacta de errores.

## Pruebas de contrato de colectores

```bash
pytest -q tests/test_collector_contract.py
```

Valida que:
- se guarden raw payloads en disco,
- los errores no se oculten,
- se deduplique payload repetido,
- la validación de archivo de sesión falle explícitamente cuando la casa no existe.
