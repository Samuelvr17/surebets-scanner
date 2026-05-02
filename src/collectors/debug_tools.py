"""Herramientas de depuración local para ejecutar un collector individual."""

from __future__ import annotations

import argparse
import json
import time
from importlib import import_module
from pathlib import Path

from src.collectors.base import BaseBookmakerCollector
from src.config.settings import BOOKMAKERS, build_app_config


def _resolve_collector_class(bookmaker: str) -> type[BaseBookmakerCollector]:
    module = import_module(f"src.collectors.{bookmaker}")
    return getattr(module, "Collector")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ejecuta un solo collector con trazas de depuración en tiempo real."
    )
    parser.add_argument("bookmaker", choices=BOOKMAKERS)
    parser.add_argument(
        "--show-files",
        action="store_true",
        help="Muestra ruta y tamaño de cada JSON guardado en disco.",
    )
    parser.add_argument(
        "--show-payload",
        action="store_true",
        help="Imprime payload completo por captura (puede ser grande).",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = build_app_config()
    bookmaker_cfg = config.bookmakers[args.bookmaker]

    collector_cls = _resolve_collector_class(args.bookmaker)
    collector = collector_cls(runtime=config.runtime, bookmaker_config=bookmaker_cfg)

    print(f"▶ Iniciando collector: {args.bookmaker}")
    print(f"  - Raw dump dir: {config.runtime.raw_dump_dir}")
    print(f"  - Session file: {bookmaker_cfg.session_state_file}")

    wall_start = time.perf_counter()
    result = collector.collect()
    elapsed = time.perf_counter() - wall_start

    print("\n=== RESUMEN ===")
    print(f"bookmaker: {result.bookmaker}")
    print(f"duración (wall): {elapsed:.2f}s")
    print(f"capturas: {len(result.captures)}")
    print(f"duplicados descartados: {result.duplicates_discarded}")
    print(f"errores: {len(result.errors)}")

    if result.errors:
        print("\n=== ERRORES ===")
        for idx, err in enumerate(result.errors, start=1):
            print(f"{idx}. {err}")

    if result.captures:
        print("\n=== CAPTURAS ===")
        for idx, cap in enumerate(result.captures, start=1):
            print(
                f"{idx}. event_id={cap.source_event_id} hash={cap.payload_hash[:12]} "
                f"saved={cap.raw_file_path}"
            )
            if args.show_files:
                file_size = Path(cap.raw_file_path).stat().st_size
                print(f"   bytes={file_size}")
            if args.show_payload:
                print(json.dumps(cap.payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
