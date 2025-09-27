"""Quick demo to instantiate the migration chemicals and inspect them."""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PKGS = ROOT / "pkgs"

def _ensure_local_packages() -> None:
    sys.path.insert(0, str(PKGS / "biosteam" / "src"))
    sys.path.insert(0, str(PKGS / "thermosteam" / "src"))

try:
    import thermosteam  # noqa: F401
except ImportError:
    _ensure_local_packages()
else:
    if not hasattr(thermosteam, "Chemical"):
        # Editable install still exposes nested layout; fall back to source tree.
        _ensure_local_packages()

try:
    from migration.thermo_setup import set_migration_thermo
except ImportError as error:  # pragma: no cover - runtime convenience
    missing = getattr(error, "name", None) or "required dependency"
    print(
        "Failed to import migration thermodynamics helpers. "
        f"Missing Python package: {missing}.\n"
        "Install the project dependencies (pip install -e pkgs/thermosteam) "
        "before running this demo."
    )
    raise SystemExit(1) from error

chemicals = set_migration_thermo()
print(f"Loaded {len(chemicals)} chemicals")
print("Key components:")
for name in ("Osteopontin", "Chitosan", "Yeast", "Glucose", "Acetic acid"):
    chem = chemicals[name]
    phase = getattr(chem, "phase", None) or getattr(chem, "phase_ref", "?")
    print(f"- {name}: MW={chem.MW:.2f}, phase={phase}")
