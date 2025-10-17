from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, TYPE_CHECKING

import biosteam as bst
import thermosteam as tmo

from .builder import build_system, BuildResult
# Apply compatibility shims early so downstream imports use patched behavior
try:
    from . import compat_shims  # noqa: F401
except Exception:
    pass

if TYPE_CHECKING:  # pragma: no cover - imported only when type checking
    from ..models.scenario import Scenario
else:  # pragma: no cover - allows running without pydantic installed
    Scenario = Any  # type: ignore[misc, assignment]


def _safe_product_mass(stream: bst.Stream) -> float:
    for component in ("Osteopontin", "Product"):
        try:
            return float(stream.imass[component])
        except Exception:
            continue
    return 0.0


def _safe_glucose_mass(stream: bst.Stream) -> float:
    try:
        return float(stream.imass["Glucose"])
    except Exception:
        return 0.0


def _terminal_units(build: BuildResult) -> List[str]:
    sources = {upstream for upstream, _ in build.streams}
    return [uid for uid in build.unit_map if uid not in sources]


def run_deterministic(scenario: Scenario) -> dict:
    build = build_system(scenario)
    build.system.simulate()

    feed_product = sum(_safe_product_mass(s) for s in build.feed_streams)
    feed_glucose = sum(_safe_glucose_mass(s) for s in build.feed_streams)
    terminal_ids = _terminal_units(build)
    terminal_streams = []
    for uid in terminal_ids:
        unit = build.unit_map[uid]
        index = int(getattr(unit, "product_outlet_index", 0))
        terminal_streams.append(unit.outs[index])
    final_product_mass = sum(_safe_product_mass(s) for s in terminal_streams)

    operating_hours = float(scenario.assumptions.get("operating_hours_per_year", 8_000.0))
    electricity_price = float(scenario.assumptions.get("electricity_price_usd_per_kwh", 0.11))
    cmo_day_rate = float(scenario.assumptions.get("cmo_day_rate_usd", 0.0))
    campaign_days = float(
        scenario.assumptions.get("campaign_days", operating_hours / 24.0)
    )

    total_power_kw = sum(getattr(unit, "power_kW", 0.0) for unit in build.unit_map.values())
    annual_energy_cost = total_power_kw * operating_hours * electricity_price
    annual_cmo_cost = cmo_day_rate * campaign_days
    annual_throughput = final_product_mass * operating_hours
    total_operating_cost = annual_energy_cost + annual_cmo_cost

    cog_per_kg = None
    if annual_throughput > 0.0:
        cog_per_kg = total_operating_cost / annual_throughput

    overall_yield = None
    basis_mass = feed_product if feed_product > 0.0 else feed_glucose
    if basis_mass > 0.0:
        overall_yield = final_product_mass / basis_mass

    unit_metadata: Dict[str, Dict[str, object]] = {}
    for uid, unit in build.unit_map.items():
        info = getattr(unit, "metadata_dict", None)
        if callable(info):
            unit_metadata[uid] = info()
        elif isinstance(info, dict):
            unit_metadata[uid] = info
        else:
            unit_metadata[uid] = {"class": unit.__class__.__name__}

    result = {
        "scenario": scenario.name,
        "timestamp": datetime.utcnow().isoformat(),
        "kpis": {
            "cog_per_kg": cog_per_kg,
            "annual_throughput_kg": annual_throughput,
            "overall_yield": overall_yield,
        },
        "mass_balance": {
            "feed_product_kg_per_hr": feed_product,
            "feed_glucose_kg_per_hr": feed_glucose,
            "final_product_kg_per_hr": final_product_mass,
        },
        "energy": {
            "total_power_kW": total_power_kw,
            "annual_energy_cost_usd": annual_energy_cost,
        },
        "assumptions": scenario.assumptions,
        "units": unit_metadata,
        "engine": {
            "biosteam_version": getattr(bst, "__version__", "local"),
            "thermosteam_version": getattr(tmo, "__version__", "local"),
            "git_hash": "local",
        },
    }

    return result
