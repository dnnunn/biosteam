"""Diagnostic CLI for inspecting module defaults and plans."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from ..excel_defaults import ExcelModuleDefaults, ModuleKey
from ..module_builders import build_module_data
from ..unit_builders import PLAN_BUILDERS, UnitPlan


def _print_header(title: str) -> None:
    print("\n" + title)
    print("-" * len(title))


def _format_value(value):
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def list_modules(loader: ExcelModuleDefaults, active_only: bool) -> None:
    _print_header("Module Options")
    for key in loader.iter_module_keys(active_only=active_only):
        config = loader.load_defaults().get(key)
        status = "active" if config and config.active else "inactive"
        print(f"{key.module}:{key.option or '<default>'} ({status})")


def show_module(loader: ExcelModuleDefaults, module: str, option: str | None, as_plan: bool) -> None:
    key = ModuleKey(module, option)
    config = loader.get_module_config(key)
    if config is None:
        print(f"No defaults found for {module}:{option or '<default>'}")
        return

    data = build_module_data(config)

    if as_plan and module in PLAN_BUILDERS:
        builder, _ = PLAN_BUILDERS[module]
        plan = builder(config)
        assert isinstance(plan, UnitPlan)
        _print_header(f"{module}:{option or plan.key.option or '<default>'} (UnitPlan)")
        print("Specs:")
        for field, value in plan.specs.__dict__.items():
            if field == "key":
                continue
            print(f"  {field}: {_format_value(value)}")
        if plan.derived:
            print("Derived:")
            for field, value in plan.derived.items():
                print(f"  {field}: {_format_value(value)}")
        if plan.notes:
            print("Notes:")
            for note in plan.notes:
                print(f"  - {note}")
    else:
        _print_header(f"{module}:{option or '<default>'} (ModuleData)")
        print("Fields:")
        for name, record in data.records.items():
            print(
                f"  {name}: value={_format_value(record.value)}"
                + (f", unit={record.unit}" if record.unit else "")
                + (f" (row {record.source_row})" if record.source_row else "")
            )


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--defaults",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "module_defaults.yaml",
        help="Path to the module defaults snapshot (YAML)",
    )
    parser.add_argument("--module", help="Module identifier (e.g., USP00)")
    parser.add_argument("--option", help="Module option (e.g., USP00a)")
    parser.add_argument(
        "--include-inactive",
        action="store_true",
        help="Include inactive module options when listing",
    )
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Render output using registered UnitPlan builders when available",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available module/options instead of printing values",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    loader = ExcelModuleDefaults(args.defaults)

    if args.list or not args.module:
        list_modules(loader, active_only=not args.include_inactive)
        if not args.module:
            return

    show_module(loader, args.module, args.option, as_plan=args.plan)


if __name__ == "__main__":  # pragma: no cover
    main()
