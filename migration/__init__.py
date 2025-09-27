"""Utilities to support BetterDairy's BioSTEAM migration efforts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .unit_builders import PLAN_BUILDERS, UnitPlan, register_baseline_unit_builders
from .chemicals import create_migration_chemicals
from .thermo_setup import set_migration_thermo
from .front_end import FrontEndSection, build_front_end_section

if TYPE_CHECKING:  # pragma: no cover - import-time convenience for type checkers
    from .unit_factories import register_plan_backed_unit_factories
else:
    try:
        from .unit_factories import register_plan_backed_unit_factories
    except ModuleNotFoundError as exc:  # pragma: no cover - deferred dependency
        _IMPORT_ERROR = exc

        def register_plan_backed_unit_factories(*args, **kwargs):
            raise ModuleNotFoundError(
                "register_plan_backed_unit_factories requires BioSTEAM and its "
                "dependencies (e.g., numba) to be installed."
            ) from _IMPORT_ERROR


__all__ = [
    "UnitPlan",
    "register_baseline_unit_builders",
    "PLAN_BUILDERS",
    "register_plan_backed_unit_factories",
    "create_migration_chemicals",
    "set_migration_thermo",
    "FrontEndSection",
    "build_front_end_section",
]
