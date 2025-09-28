"""Quick demo to build and simulate the upstream (front-end) section."""

from __future__ import annotations

import argparse
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
PKGS = ROOT / "pkgs"


def _ensure_local_packages() -> None:
    candidate_paths = (
        PKGS / "biosteam" / "src",
        PKGS / "thermosteam" / "src",
        PKGS / "thermosteam" / "src" / "thermosteam",
    )
    for path in candidate_paths:
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


_ensure_local_packages()

try:
    import biosteam  # noqa: F401
    import thermosteam  # noqa: F401
except ImportError as exc:  # pragma: no cover - environment safeguard
    raise SystemExit(
        "Unable to import local biosteam/thermosteam packages; "
        "ensure pkgs/biosteam and pkgs/thermosteam are present."
    ) from exc


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
        default=None,
        help="Override working volume in litres (defaults to workbook value)",
    )
    args = parser.parse_args()

    if args.workbook is None:
        raise SystemExit(
            "Please supply the path to the Excel workbook, e.g.\n"
            "  python -m scripts.demo_front_end /path/to/Revised\\ Model.xlsx"
        )

    kwargs = {}
    if args.volume is not None:
        kwargs["batch_volume_l"] = args.volume
    section = build_front_end_section(args.workbook, **kwargs)
    section.simulate()

    print("\nFront-end simulation complete. Key stream summaries:")
    _summarise(section.feed, "Seed feed")
    _summarise(section.seed_unit.outs[0], "Seed effluent")
    _summarise(section.fermentation_unit.outs[0], "Fermentation broth")
    _summarise(section.microfiltration_unit.outs[0], "Post-MF supernatant")
    _summarise(section.ufdf_unit.outs[0], "Post-UF/DF concentrate")
    _summarise(section.chromatography_unit.outs[0], "Post-chromatography eluate")
    _summarise(section.predrying_unit.outs[0], "Post pre-drying TFF")
    _summarise(section.spray_dryer_unit.outs[0], "Final dried product")


if __name__ == "__main__":
    main()
