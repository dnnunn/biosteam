"""Quick sanity check for the baseline system builder.

This script registers placeholder builders for the default module sequence and
attempts to assemble the baseline system using the static defaults snapshot
(``module_defaults.yaml``).  It is intended purely for integration bring-up;
replace the placeholder builders with real BioSTEAM factories once ready.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

from .baseline_system import DEFAULT_MODULE_SEQUENCE, build_baseline_system
from .excel_defaults import ExcelModuleDefaults
from .module_builders import ModuleData, register_data_builders
from .module_registry import ModuleRegistry


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--defaults",
        type=Path,
        default=Path(__file__).with_name("module_defaults.yaml"),
        help="Path to the module defaults snapshot (YAML)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    registry = ModuleRegistry()

    register_data_builders(registry, DEFAULT_MODULE_SEQUENCE, description="normalized module data")

    try:
        system = build_baseline_system(
            args.defaults,
            registry=registry,
            defaults_loader=ExcelModuleDefaults(args.defaults),
        )
    except FileNotFoundError as exc:
        print(exc)
        print("\nHint: ensure the module defaults snapshot exists or provide the full path.")
        return

    print("Baseline system assembled with the following modules:\n")
    for key, module_data in system.units.items():
        assert isinstance(module_data, ModuleData)
        print(
            f"- {key.module} ({key.option or 'default'}): "
            f"{len(module_data.records)} parameters, {len(module_data.values)} normalized values"
        )


if __name__ == "__main__":
    main()
