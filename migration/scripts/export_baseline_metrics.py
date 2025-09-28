"""CLI to snapshot the Excel baseline KPIs into the regression fixture."""

from __future__ import annotations

import argparse
from pathlib import Path

from migration.baseline_metrics import export_baseline_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workbook",
        type=Path,
        default=Path("BaselineModel.xlsx"),
        help="Path to the Excel workbook (default: %(default)s).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("migration/baseline_metrics_map.yaml"),
        help="Cell mapping file (default: %(default)s).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tests/opn/baseline_metrics.json"),
        help="Destination JSON file (default: %(default)s).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metrics = export_baseline_metrics(
        workbook_path=args.workbook,
        config_path=args.config,
        output_path=args.output,
    )
    print(f"Wrote baseline metrics to {args.output.resolve()}")
    print(f"Final product per batch: {metrics.final_product_kg:.3f} kg")
    if metrics.cost_per_kg_usd is not None:
        print(f"Cost per kg: ${metrics.cost_per_kg_usd:.2f}")
    else:
        print("Cost per kg not recorded; update migration/baseline_metrics_map.yaml")


if __name__ == "__main__":
    main()
