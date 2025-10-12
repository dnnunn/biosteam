from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, TYPE_CHECKING

import biosteam as bst

from .registry import get_factory
from migration.thermo_setup import set_migration_thermo

if TYPE_CHECKING:  # pragma: no cover - imported only for type checking
    from ..models.scenario import Scenario
else:  # pragma: no cover - fallback for runtime without pydantic
    Scenario = Any  # type: ignore[misc, assignment]


@dataclass
class BuildResult:
    system: bst.System
    unit_map: Dict[str, bst.Unit]
    streams: Dict[Tuple[str, str], bst.Stream]
    feed_streams: List[bst.Stream]
    order: List[str]


_THERMO_INITIALISED = False


def _ensure_thermo(package_name: str | None = None) -> None:
    global _THERMO_INITIALISED
    if _THERMO_INITIALISED:
        return

    chemicals = set_migration_thermo()
    if package_name:
        bst.settings.thermo.user_data["package"] = package_name
    _THERMO_INITIALISED = True


def _to_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _feed_components_for_unit(
    unit: bst.Unit,
    base_mass: float,
    product_fraction: float,
) -> Dict[str, float]:
    plan = getattr(unit, "plan", None)
    derived = getattr(plan, "derived", None)
    if not isinstance(derived, dict):
        glucose_mass = base_mass * product_fraction
        water_mass = max(base_mass - glucose_mass, 0.0)
        yeast_mass = max(base_mass * 0.01, 0.0)
        return {
            "Glucose": glucose_mass,
            "Water": water_mass,
            "Yeast": yeast_mass,
            "Waste": 0.0,
        }

    glucose_rate = _to_float(derived.get("glucose_feed_rate_kg_per_hr"))
    if glucose_rate is None:
        glucose_rate = base_mass * product_fraction

    cycle_hours = _to_float(derived.get("batch_cycle_hours"))
    if cycle_hours is None:
        cycle_hours = _to_float(derived.get("seed_train_duration_hours"))

    yeast_rate = _to_float(derived.get("initial_biomass_feed_rate_kg_per_hr"))
    if yeast_rate is None:
        inoculum = _to_float(derived.get("initial_biomass_kg"))
        if inoculum is not None and cycle_hours and cycle_hours > 0.0:
            yeast_rate = inoculum / cycle_hours
        else:
            yeast_rate = base_mass * 0.01

    volume_l = _to_float(derived.get("working_volume_l"))
    density = _to_float(derived.get("broth_density_kg_per_l"))

    water_rate = max(base_mass - glucose_rate, 0.0)
    if volume_l and density and cycle_hours and cycle_hours > 0.0:
        total_rate = (volume_l * density) / cycle_hours
        water_rate = max(total_rate - glucose_rate - max(yeast_rate, 0.0), 0.0)

    return {
        "Glucose": max(glucose_rate, 0.0),
        "Water": max(water_rate, 0.0),
        "Yeast": max(yeast_rate, 0.0),
    }


def _autowire_streams_if_missing(scenario: Scenario) -> List[Tuple[str, str]]:
    if scenario.streams:
        return [(s.from_, s.to) for s in scenario.streams]
    ids = [u.id for u in scenario.units]
    return list(zip(ids[:-1], ids[1:]))


def _topological_order(unit_ids: List[str], links: List[Tuple[str, str]]) -> List[str]:
    outgoing: Dict[str, List[str]] = defaultdict(list)
    incoming_count: Dict[str, int] = {u: 0 for u in unit_ids}
    for upstream, downstream in links:
        outgoing[upstream].append(downstream)
        incoming_count[downstream] = incoming_count.get(downstream, 0) + 1
        incoming_count.setdefault(upstream, 0)

    queue = deque([u for u, count in incoming_count.items() if count == 0])
    order: List[str] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for child in outgoing.get(node, []):
            incoming_count[child] -= 1
            if incoming_count[child] == 0:
                queue.append(child)

    if len(order) != len(incoming_count):
        raise ValueError("Scenario contains a cycle; unable to build system")
    return order


def build_system(scenario: Scenario) -> BuildResult:
    _ensure_thermo(scenario.thermo_package)

    unit_map: Dict[str, bst.Unit] = {}
    for unit_spec in scenario.units:
        factory = get_factory(unit_spec.template)
        unit_map[unit_spec.id] = factory(id=unit_spec.id, **(unit_spec.overrides or {}))

    links = _autowire_streams_if_missing(scenario)
    order = _topological_order([u.id for u in scenario.units], links)

    streams: Dict[Tuple[str, str], bst.Stream] = {}
    incoming_map: Dict[str, List[str]] = defaultdict(list)
    outgoing_map: Dict[str, List[str]] = defaultdict(list)
    for upstream, downstream in links:
        incoming_map[downstream].append(upstream)
        outgoing_map[upstream].append(downstream)
        source_unit = unit_map[upstream]
        sink_unit = unit_map[downstream]

        stream = bst.Stream(f"{upstream}_to_{downstream}")
        product_index = int(getattr(source_unit, "product_outlet_index", 0))
        if len(source_unit.outs) > product_index:
            source_unit.outs[product_index] = stream
        elif len(source_unit.outs) >= 1:
            source_unit.outs[0] = stream
        else:
            source_unit.outs[:] = [stream]
        if len(sink_unit.ins) >= 1:
            sink_unit.ins[0] = stream
        else:
            sink_unit.ins[:] = [stream]
        streams[(upstream, downstream)] = stream

    feed_streams: List[bst.Stream] = []
    feed_mass = float(scenario.assumptions.get("feed_mass_flow_kg_per_hr", 1000.0))
    product_fraction = float(scenario.assumptions.get("product_mass_fraction", 0.05))
    start_units = [u_id for u_id in unit_map if not incoming_map.get(u_id)]
    for u_id in start_units:
        unit = unit_map[u_id]
        components = _feed_components_for_unit(unit, feed_mass, product_fraction)
        feed_stream = bst.Stream(
            f"{u_id}_feed",
            units="kg/hr",
            **components,
        )
        if len(unit.ins) >= 1:
            unit.ins[0] = feed_stream
        else:
            unit.ins[:] = [feed_stream]
        feed_streams.append(feed_stream)

    system_units = [unit_map[u_id] for u_id in order]
    system = bst.System(scenario.name or "scenario_system", path=system_units)

    build_result = BuildResult(
        system=system,
        unit_map=unit_map,
        streams=streams,
        feed_streams=feed_streams,
        order=order,
    )
    return build_result
