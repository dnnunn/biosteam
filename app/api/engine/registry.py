# Maps template names to callables returning BioSTEAM-compatible unit stubs.
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable

from .simple_units import ScenarioUnit
from . import migration_factories

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    import biosteam as bst

UnitFactory = Callable[..., "bst.Unit"]

DEFAULT_TEMPLATE_DESCRIPTORS: Dict[str, Dict[str, Any]] = {
    "SeedFermenter_v1": {
        "category": "USP",
        "defaults": {
            "working_volume_m3": 7.0,
            "temp_C": 30.0,
            "pH": 5.5,
            "time_h": 18.0,
            "yield_fraction": 0.95,
            "power_kW": 5.0,
            "dcw_concentration_g_L": 10.0,
            "broth_density_kg_per_l": 1.05,
        },
    },
    "ProdFermenter_v2": {
        "category": "USP",
        "defaults": {
            "working_volume_m3": 70.0,
            "titer_g_L": 5.0,
            "glucose_g_L": 100.0,
            "temp_C": 30.0,
            "time_h": 72.0,
            "yield_fraction": 0.90,
            "power_kW": 22.0,
            "broth_density_kg_per_l": 1.05,
            "od_to_dcw_g_per_l_per_od": 0.4,
        },
    },
    "DiskStack_v1": {
        "category": "Primary Recovery",
        "defaults": {
            "flow_m3_h": 5.0,
            "yield_fraction": 0.98,
            "power_kW": 15.0,
        },
    },
    "MF_Polishing_v1": {
        "category": "Primary Recovery",
        "defaults": {
            "area_m2": 20.0,
            "flux_L_m2_h": 60.0,
            "yield_fraction": 0.99,
            "TMP_bar": 1.0,
            "power_kW": 8.0,
            "broth_density_kg_per_l": 1.05,
        },
    },
    "AEX_Column_v1": {
        "category": "DSP04",
        "defaults": {
            "resin_capacity_g_L": 50.0,
            "bed_volume_L": 10.0,
            "flow_BV_h": 3.0,
            "yield_fraction": 0.85,
            "resin_cost_usd_per_L": 800.0,
            "cip_time_h": 0.5,
            "lifetime_cycles": 50,
            "power_kW": 6.0,
        },
    },
    "ChitosanCapture_v1": {
        "category": "DSP04",
        "defaults": {
            "polymer_type": "LMW",
            "polymer_pct_wv": 0.1,
            "target_pH": 4.4,
            "NaCl_mM": 250,
            "stoichiometry_mass_ratio": 2.0,
            "contact_time_min": 15.0,
            "yield_fraction": 0.80,
            "dna_reduction_log": 2.0,
            "polymer_cost_usd_per_kg": 18.0,
            "recycle_fraction": 0.5,
            "power_kW": 10.0,
        },
    },
    "UFDF_v1": {
        "category": "Finishing",
        "defaults": {
            "area_m2": 10.0,
            "flux_L_m2_h": 40.0,
            "cff": 3.0,
            "yield_fraction": 0.95,
            "membrane_cost_usd_m2": 220.0,
            "lifetime_cycles": 20,
            "power_kW": 9.0,
            "broth_density_kg_per_l": 1.05,
        },
    },
    "PreDry_TFF_v1": {
        "category": "Finishing",
        "defaults": {
            "area_m2": 25.0,
            "flux_L_m2_h": 35.0,
            "cff": 5.0,
            "yield_fraction": 0.95,
            "membrane_cost_usd_m2": 260.0,
            "lifetime_cycles": 15,
            "broth_density_kg_per_l": 1.05,
            "power_kW": 14.0,
        },
    },
    "SterileFilter_v1": {
        "category": "DSP04",
        "defaults": {
            "flux_lmh": 250.0,
            "max_dp_bar": 1.5,
            "adsorption_loss_fraction": 0.0,
            "prefilter_enabled": False,
            "yield_fraction": 1.0,
            "power_kW": 4.0,
        },
    },
    "SprayDry_v1": {
        "category": "Finishing",
        "defaults": {
            "evap_rate_kg_h": 100.0,
            "inlet_C": 180.0,
            "outlet_C": 90.0,
            "yield_fraction": 0.985,
            "energy_kWh_per_kg_water": 0.8,
            "power_kW": 18.0,
            "final_solids_percent": 12.0,
            "solution_density": 1.05,
        },
    },
}

_registry: Dict[str, UnitFactory] = {}


def register(template: str, factory: UnitFactory) -> None:
    """Register a unit factory for a scenario template."""

    if template in _registry:
        raise ValueError(f"Template already registered: {template}")
    _registry[template] = factory


def get_factory(template: str) -> UnitFactory:
    """Return a previously registered unit factory."""

    try:
        return _registry[template]
    except KeyError as exc:
        raise KeyError(f"Unit template not registered: {template}") from exc


def all_templates() -> Dict[str, UnitFactory]:
    """Return the raw registry (read-only callers should copy if mutating)."""

    return dict(_registry)


def _make_factory(template: str, *, category: str, defaults: Dict[str, Any]) -> UnitFactory:
    """Create a ScenarioUnit factory with template-specific defaults."""

    def factory(id: str, **overrides: Any) -> ScenarioUnit:
        merged = dict(defaults)
        merged.update(overrides or {})
        yield_fraction = float(merged.get("yield_fraction", 1.0))
        power_kW = float(merged.get("power_kW", 0.0))
        residence_time_h = merged.get("residence_time_h")
        return ScenarioUnit(
            id,
            template=template,
            category=category,
            yield_fraction=yield_fraction,
            power_kW=power_kW,
            residence_time_h=(
                float(residence_time_h) if residence_time_h is not None else None
            ),
            metadata_defaults=dict(merged),
        )

    return factory


def register_defaults(extra_templates: Iterable[tuple[str, Dict[str, Any]]] | None = None) -> None:
    """Register the default set of template factories used by the UI demo."""

    _registry.clear()
    templates: Dict[str, Dict[str, Any]] = dict(DEFAULT_TEMPLATE_DESCRIPTORS)

    if extra_templates:
        for template, descriptor in extra_templates:
            templates[template] = descriptor

    for template, descriptor in templates.items():
        descriptor_copy = dict(descriptor)
        defaults = dict(descriptor_copy.get("defaults") or {})
        descriptor_copy["defaults"] = defaults

        if migration_factories.supports(template):
            factory = migration_factories.create_factory(template, descriptor_copy)
        else:
            factory = _make_factory(
                template,
                category=descriptor_copy["category"],
                defaults=defaults,
            )
        _registry[template] = factory


# Make sure defaults are available as soon as the module is imported.
register_defaults()
