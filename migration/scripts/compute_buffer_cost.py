from __future__ import annotations

"""Estimate buffer material cost [USD/m3] from the curated registry.

Usage:
  python -m migration.scripts.compute_buffer_cost --id tris_hcl_pH7p5_50mM
"""

import argparse

from migration.buffer_tools.costing import estimate_cost_per_m3_for_buffer_id


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--id", required=True, help="Buffer registry ID")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cost = estimate_cost_per_m3_for_buffer_id(args.id)
    if cost is None:
        print(f"No reagent breakdown available for buffer id '{args.id}'.")
    else:
        print(f"Estimated cost: ${cost:.2f} per m3 for '{args.id}'.")


if __name__ == "__main__":  # pragma: no cover
    main()

