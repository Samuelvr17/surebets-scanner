"""Punto de entrada para ejecutar localmente el scanner de surebets."""

from __future__ import annotations

import argparse
import json

from src.collectors.session_manager import save_manual_session_state
from src.config.settings import build_app_config
from src.pipeline import run_capture_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Surebets scanner - captura prematch")
    parser.add_argument(
        "--save-session",
        choices=[
            "betplay",
            "rushbet",
            "stake_colombia",
            "codere_colombia",
            "sportium_colombia",
        ],
        help="Abre navegador visible para login manual y guarda storage_state.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_app_config()

    if args.save_session:
        filepath = save_manual_session_state(config, args.save_session)
        print(f"Sesión guardada: {filepath}")
        return

    results = run_capture_pipeline(config)
    output = [
        {
            "bookmaker": r.bookmaker,
            "captures": len(r.captures),
            "duplicates_discarded": r.duplicates_discarded,
            "errors": r.errors,
            "started_at_utc": r.started_at_utc.isoformat(),
            "finished_at_utc": r.finished_at_utc.isoformat(),
        }
        for r in results
    ]
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
