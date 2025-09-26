"""Factories that convert UnitPlans into simple BioSTEAM units."""

from __future__ import annotations

from typing import Dict, Iterable, Tuple

import biosteam as bst

from .excel_defaults import ModuleKey
from .module_registry import ModuleRegistry
from .unit_builders import PLAN_BUILDERS, UnitPlan
from .simple_units import (
    FermentationUnit,
    SeedTrainUnit,
    MicrofiltrationUnit,
    UFDFUnit,
    ChromatographyUnit,
    PreDryingUnit,
    SprayDryerUnit,
)

__all__ = [
    "register_plan_backed_unit_factories",
]


PLAN_UNIT_CLASSES: Dict[str, Tuple[type, str]] = {
    "USP00": (FermentationUnit, "Fermenter"),
    "USP01": (SeedTrainUnit, "SeedTrain"),
    "USP02": (MicrofiltrationUnit, "USP02"),
    "DSP01": (UFDFUnit, "DSP01"),
    "DSP02": (ChromatographyUnit, "DSP02"),
    "DSP03": (PreDryingUnit, "DSP03"),
    "DSP05": (SprayDryerUnit, "DSP05"),
}


def _make_unit_id(plan: UnitPlan, prefix: str) -> str:
    option = plan.key.option or "default"
    return f"{prefix}_{option}"


def _build_unit_from_plan(plan: UnitPlan, module: str) -> bst.Unit:
    cls, prefix = PLAN_UNIT_CLASSES[module]
    unit_id = _make_unit_id(plan, prefix)
    unit = cls(unit_id, plan=plan)
    return unit


def register_plan_backed_unit_factories(
    registry: ModuleRegistry,
    *,
    module_options: Dict[str, Iterable[str]] | None = None,
) -> None:
    """Register factories that return simple BioSTEAM units from plans."""

    module_options = module_options or {}
    for module, (plan_builder, default_options) in PLAN_BUILDERS.items():
        if module not in PLAN_UNIT_CLASSES:
            continue  # Not yet supported
        options = tuple(module_options.get(module, default_options))
        for option in options:
            key = ModuleKey(module, option)

            def builder(config, _plan_builder=plan_builder, _module=module):
                plan = _plan_builder(config)
                return _build_unit_from_plan(plan, _module)

            registry.register(
                key,
                builder,
                description=f"Plan-backed unit for {module}",
                overwrite=True,
            )
