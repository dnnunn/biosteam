from __future__ import annotations

from fastapi import APIRouter, Query
from pathlib import Path
import json
from typing import Any, Dict, List

from migration.buffer_tools.costing import estimate_cost_per_m3_for_buffer_id


router = APIRouter()
BUFFERS_PATH = Path("migration/data_sources/buffers.json")


def _load_buffers() -> List[Dict[str, Any]]:
    if not BUFFERS_PATH.exists():
        return []
    try:
        data = json.loads(BUFFERS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else []


@router.get("")
def list_buffers(include_cost: bool = Query(default=True)) -> List[Dict[str, Any]]:
    """Return curated buffer recipes for UI dropdowns.

    Fields: id, name, pH, temperature_C, components (name, concentration_mM, charge_z),
    and optional estimated_cost_usd_per_m3 when include_cost is true and reagents exist.
    """
    items = []
    for entry in _load_buffers():
        if not isinstance(entry, dict):
            continue
        item = {
            "id": entry.get("id"),
            "name": entry.get("name"),
            "pH": entry.get("pH"),
            "temperature_C": entry.get("temperature_C"),
            "components": entry.get("components"),
        }
        if include_cost:
            try:
                cost = estimate_cost_per_m3_for_buffer_id(str(entry.get("id")))
            except Exception:
                cost = None
            if isinstance(cost, (int, float)):
                item["estimated_cost_usd_per_m3"] = float(cost)
        items.append(item)
    return items

