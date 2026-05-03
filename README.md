# Surebets Scanner (Consola)

Arquitectura modular para detectar surebets desde múltiples fuentes (snapshots locales, API autorizada y adaptadores por bookmaker), manteniendo el MVP local.

## Núcleo del motor
- Normalización: `src/normalizers/odds_normalizer.py`
- Matching de eventos: `src/matchers/event_matcher.py`
- Detección surebet: `src/arbitrage/surebet_engine.py`
- Revalidación: `src/arbitrage/revalidation.py`
- Orquestación: `src/pipeline.py`

## Formato canónico
Cada fila canónica (`CanonicalOdd`) incluye: bookmaker, sport, league, equipos, hora UTC, family/period/side, línea, selección, odds decimal y timestamp de captura.

## Ejecutar modo snapshots (MVP)
```bash
python -m src.main --input-dir data/input_snapshots --initial snapshot_t0 --latest snapshot_t1_valid
python -m src.main scan --input-dir data/input_snapshots --initial snapshot_t0 --latest snapshot_t1_valid
```

## Fuentes configurables
Archivo ejemplo: `config/sources.example.yml`.
Tipos soportados:
- `local_snapshot`
- `authorized_api`
- `bookmaker_adapter`

## Healthcheck
```bash
python -m src.main health --config config/sources.example.yml
```

## Validar perfil de bookmaker
```bash
python -m src.main validate-profile --profile config/profiles/betplay.example.yml --sample data/samples/betplay_sample.json
```

## Extender una nueva casa sin tocar motor
1. Crear `config/profiles/<casa>.example.yml` con paths raw->canónico.
2. Implementar fetch en `BookmakerSource` o nuevo `OddsSource`.
3. Mantener salida en rows canónicas (o usar `profile_mapper`).
4. El pipeline sigue igual.
