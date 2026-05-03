# Surebets Scanner MVP (Consola)

MVP local por consola para leer snapshots JSON y detectar/revalidar surebets.

## Instalar dependencias

```bash
pip install -r requirements.txt
```

## Correr tests

```bash
pytest -q
```

## Ejecutar scanner por consola

```bash
python -m src.main --input-dir data/input_snapshots --initial snapshot_t0 --latest snapshot_t1_valid
python -m src.main --input-dir data/input_snapshots --initial snapshot_t0 --latest snapshot_t1_expired
```
