"""Quick demo to build and simulate the upstream (front-end) section."""

from __future__ import annotations

import argparse
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
PKGS = ROOT / "pkgs"


def _ensure_local_packages() -> None:
    sys.path.insert(0, str(PKGS / "biosteam" / "src"))
    sys.path.insert(0, str(PKGS / "thermosteam" / "src"))


try:
    import biosteam  # noqa: F401
except ImportError:
    _ensure_local_packages()
else:
    try:
        import thermosteam  # noqa: F401
    except ImportError:
        _ensure_local_packages()


from migration.front_end import build_front_end_section


def _summarise(stream, label):
    components = {}
    for name in ("Glucose", "Yeast", "Osteopontin", "Water"):
        try:
            mass = float(stream.imass[name])
        except Exception:  # pragma: no cover - component absent
            mass = 0.0
        if mass:
            components[name] = mass
    total = stream.F_mass
    parts = ", ".join(f"{name}={mass:.2f} kg" for name, mass in components.items())
    print(f"{label}: total={total:.2f} kg -> {parts}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "workbook",
        nargs="?",
        help="Path to the Excel defaults workbook",
    )
    parser.add_argument(
        "--volume",
        type=float,
        default=1_000.0,
        help="Assumed batch volume in litres for the placeholder media",
    )
    args = parser.parse_args()

    if args.workbook is None:
        raise SystemExit(
            "Please supply the path to the Excel workbook, e.g.\n"
            "  python -m scripts.demo_front_end /path/to/Revised\\ Model.xlsx"
        )

    section = build_front_end_section(args.workbook, batch_volume_l=args.volume)
    section.system.simulate(design_and_cost=False)

    print("\nFront-end simulation complete. Key stream summaries:")
    _summarise(section.feed, "Seed feed")
    _summarise(section.seed_unit.outs[0], "Seed effluent")
    _summarise(section.fermentation_unit.outs[0], "Fermentation broth")
    _summarise(section.harvest_unit.outs[0], "Harvested stream")


if __name__ == "__main__":
    main()
