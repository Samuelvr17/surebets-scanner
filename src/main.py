from __future__ import annotations

import argparse
from pathlib import Path

from src.pipeline import run_console_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description='Scanner MVP por consola')
    parser.add_argument('--input-dir', default='data/input_snapshots')
    parser.add_argument('--initial', default='snapshot_t0')
    parser.add_argument('--latest', default='snapshot_t1')
    args = parser.parse_args()

    rows = run_console_pipeline(Path(args.input_dir), args.initial, args.latest)
    if not rows:
        print('No se encontraron surebets válidas.')
        return
    for row in rows:
        print(row)


if __name__ == '__main__':
    main()
