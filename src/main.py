"""Punto de entrada para ejecutar localmente el scanner de surebets."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal

from src.collectors.session_manager import save_manual_session_state
from src.config.settings import build_app_config
from src.pipeline import run_capture_pipeline
from src.pipeline_end_to_end import run_full_processing_pipeline


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
    parser.add_argument(
        "--process-captures",
        action="store_true",
        help="Procesa capturas crudas ya guardadas hasta surebets revalidadas.",
    )
    parser.add_argument(
        "--budget",
        type=str,
        default="100000",
        help="Presupuesto total para cálculo de stakes (ej. 100000).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = build_app_config()

    if args.save_session:
        filepath = save_manual_session_state(config, args.save_session)
        print(f"Sesión guardada: {filepath}")
        return

    if args.process_captures:
        opportunities = run_full_processing_pipeline(config, total_budget=Decimal(args.budget))
        if not opportunities:
            print("No se encontraron surebets revalidadas.")
            return

        for idx, item in enumerate(opportunities, start=1):
            opp = item.opportunity
            print(f"\n=== SUREBET #{idx} ===")
            print(f"Evento: {opp.canonical_event_key}")
            print(f"Mercado: {opp.market_type}")
            print(f"Estado: {opp.status}")
            print(f"ROI esperado: {opp.expected_roi_percent}%")
            print("Piernas y stakes sugeridos:")
            for leg in item.stake_plan:
                print(
                    f"  - {leg.bookmaker} | {leg.selection} | cuota={leg.odds_decimal} | "
                    f"stake={leg.stake} | payout={leg.payout_if_wins}"
                )
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
