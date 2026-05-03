# Surebets Scanner MVP (Consola)

MVP local por consola para procesar snapshots JSON estructurados y detectar surebets.

## Instalar dependencias

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Correr tests

```bash
pytest -q
```

## Ejecutar scanner por consola

```bash
python -m src.main --input-dir data/input_snapshots --initial snapshot_t0 --latest snapshot_t1
```

## Procesar snapshots locales

- Coloca snapshots en `data/input_snapshots/*.json`.
- Cada archivo debe ser un array de filas canónicas con los campos estrictos:
  `bookmaker, sport, league, home_team, away_team, event_start_utc, market_family, period, side_code, line_value, line_unit, selection, odds_decimal, pulled_at_utc`.
