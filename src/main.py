from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.ingestion.source_registry import load_sources
from src.normalizers.odds_normalizer import normalize_snapshots_with_errors
from src.normalizers.profile_mapper import map_profile_payload
from src.pipeline import run_console_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description='Surebets scanner por consola')
    sub = parser.add_subparsers(dest='cmd')

    scan = sub.add_parser('scan')
    scan.add_argument('--config')
    scan.add_argument('--source')
    scan.add_argument('--input-dir')
    scan.add_argument('--initial')
    scan.add_argument('--latest')

    health = sub.add_parser('health')
    health.add_argument('--config', required=True)

    vp = sub.add_parser('validate-profile')
    vp.add_argument('--profile', required=True)
    vp.add_argument('--sample', required=True)

    parser.add_argument('--input-dir', default='data/input_snapshots')
    parser.add_argument('--initial', default='snapshot_t0')
    parser.add_argument('--latest', default='snapshot_t1_valid')

    args = parser.parse_args()

    if args.cmd == 'health':
        for s in load_sources(args.config):
            print(s.healthcheck())
        return
    if args.cmd == 'validate-profile':
        raw = json.load(open(args.sample, 'r', encoding='utf-8'))
        rows, errors = map_profile_payload(raw, args.profile, 'profile_test')
        normalized = normalize_snapshots_with_errors(rows)
        print(f'rows={len(normalized.rows)} errors={errors + normalized.errors}')
        return
    if args.cmd == 'scan' and args.config and args.source:
        source = [s for s in load_sources(args.config) if s.source_id == args.source][0]
        rows = source.fetch_snapshot()
        print(f'source={source.source_id} rows={len(rows)} (use local snapshot args for full revalidation output)')
        return

    input_dir = args.input_dir if args.cmd != 'scan' or not args.input_dir else args.input_dir
    initial = args.initial if args.cmd != 'scan' or not args.initial else args.initial
    latest = args.latest if args.cmd != 'scan' or not args.latest else args.latest
    rows = run_console_pipeline(Path(input_dir), initial, latest)
    if not rows:
        print('No se encontraron surebets validadas.')
        return
    for row in rows:
        print(row)
        print('-' * 60)


if __name__ == '__main__':
    main()
