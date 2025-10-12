from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
import json
from typing import Any, Dict, List, Optional

from migration.buffer_tools.costing import estimate_cost_per_m3_for_buffer_id
from migration.buffer_tools.buffers import BufferSpec, ionic_strength_mM, estimate_conductivity_mScm


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


def _save_buffers(entries: List[Dict[str, Any]]) -> None:
    BUFFERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    BUFFERS_PATH.write_text(json.dumps(entries, indent=2), encoding="utf-8")


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


@router.get("/{buffer_id}")
def get_buffer(buffer_id: str) -> Dict[str, Any]:
    """Return full buffer details including estimated ionic strength and conductivity."""
    for entry in _load_buffers():
        if not isinstance(entry, dict):
            continue
        if str(entry.get("id")) == str(buffer_id):
            out = dict(entry)
            try:
                spec = BufferSpec.from_mapping(entry)
                out["estimated_ionic_strength_mM"] = ionic_strength_mM(spec)
                out["estimated_conductivity_mScm"] = estimate_conductivity_mScm(spec)
            except Exception:
                pass
            try:
                cost = estimate_cost_per_m3_for_buffer_id(str(buffer_id))
            except Exception:
                cost = None
            if isinstance(cost, (int, float)):
                out["estimated_cost_usd_per_m3"] = float(cost)
            return out
    raise HTTPException(status_code=404, detail="Buffer not found")


def _hh_split(total_mM: float, pH: float, pKa: float) -> tuple[float, float]:
    """Return (acid_mM, base_mM) using Henderson–Hasselbalch for monoprotic system."""
    import math
    ratio = 10 ** (pH - pKa)
    base = total_mM * (ratio / (1.0 + ratio))
    acid = max(total_mM - base, 0.0)
    return acid, base


@router.post("")
def create_buffer(
    *,
    id: str,
    name: str,
    pH: float,
    temperature_C: float = 25.0,
    template: Optional[str] = Query(default=None, description="Optional template: 'phosphate' or 'tris_hcl'"),
    total_mM: Optional[float] = Query(default=None, description="Total buffer molarity for template-based creation"),
    components: Optional[List[Dict[str, Any]]] = None,
    reagents: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Create a new buffer recipe.

    Two modes:
    - Template mode: provide template ('phosphate' or 'tris_hcl'), total_mM, and pH; server derives components/reagents.
    - Direct mode: provide components (with name/concentration_mM/charge_z) and optional reagents (name/concentration_mM).
    """
    entries = _load_buffers()
    if any(isinstance(e, dict) and str(e.get("id")) == id for e in entries):
        raise HTTPException(status_code=400, detail="Buffer id already exists")

    record: Dict[str, Any] = {
        "id": id,
        "name": name,
        "pH": float(pH),
        "temperature_C": float(temperature_C),
    }

    if template:
        tmpl = template.strip().lower()
        if total_mM is None or total_mM <= 0.0:
            raise HTTPException(status_code=400, detail="total_mM is required for template mode")
        if tmpl == "phosphate":
            # Pair: H2PO4- (acid), HPO4^2- (base); pKa2 ~ 7.2 at 25 °C
            acid_mM, base_mM = _hh_split(total_mM, pH, pKa=7.2)
            record["components"] = [
                {"name": "Na+", "concentration_mM": total_mM, "charge_z": 1},
                {"name": "H2PO4-", "concentration_mM": acid_mM, "charge_z": -1},
                {"name": "HPO4^2-", "concentration_mM": base_mM, "charge_z": -2},
            ]
            record["reagents"] = [
                {"name": "NaH2PO4·H2O", "concentration_mM": acid_mM},
                {"name": "Na2HPO4", "concentration_mM": base_mM},
            ]
        elif tmpl == "tris_hcl":
            # Pair: TrisH+ (acid), Tris (base); pKa ~ 8.06 at 25 °C
            acid_mM, base_mM = _hh_split(total_mM, pH, pKa=8.06)
            record["components"] = [
                {"name": "TrisH+", "concentration_mM": acid_mM, "charge_z": 1},
                {"name": "Tris", "concentration_mM": base_mM, "charge_z": 0},
                {"name": "Cl-", "concentration_mM": acid_mM, "charge_z": -1},
            ]
            record["reagents"] = [
                {"name": "Tris", "concentration_mM": total_mM},
                {"name": "HCl", "concentration_mM": acid_mM},
            ]
        else:
            raise HTTPException(status_code=400, detail="Unsupported template; use 'phosphate' or 'tris_hcl'")
    else:
        if not components:
            raise HTTPException(status_code=400, detail="components are required when template is not provided")
        record["components"] = components
        if reagents:
            record["reagents"] = reagents

    # Validate and persist
    spec = BufferSpec.from_mapping(record)
    if spec is None:
        raise HTTPException(status_code=400, detail="Invalid components format")
    entries.append(record)
    _save_buffers(entries)
    # Return with derived estimates
    out = dict(record)
    out["estimated_ionic_strength_mM"] = ionic_strength_mM(spec)
    out["estimated_conductivity_mScm"] = estimate_conductivity_mScm(spec)
    cost = estimate_cost_per_m3_for_buffer_id(id)
    if isinstance(cost, (int, float)):
        out["estimated_cost_usd_per_m3"] = float(cost)
    return out


@router.get("/{buffer_id}/recommendations")
def get_buffer_recommendations(buffer_id: str) -> Dict[str, Any]:
    """Return suggested DSP03 planner targets and flags for a buffer.

    Provides opt-in defaults for ionic-strength target, conductivity target,
    DF time, headroom, ND/area caps, and a ready-to-use overrides stub.
    """
    entry = None
    for e in _load_buffers():
        if isinstance(e, dict) and str(e.get("id")) == str(buffer_id):
            entry = e
            break
    if entry is None:
        raise HTTPException(status_code=404, detail="Buffer not found")

    spec = BufferSpec.from_mapping(entry)
    I_mM = ionic_strength_mM(spec) if spec else 0.0
    kappa = estimate_conductivity_mScm(spec) if spec else 0.0

    # Heuristic targets (UI hints):
    # - Suggest reducing to 5 mM or 1 mM depending on current I
    # - Conductivity target ~5 mS/cm as a conservative post-DF value
    target_I = 5.0 if I_mM > 5.0 else max(I_mM * 0.5, 1.0)
    target_kappa = 5.0 if kappa > 5.0 else max(kappa * 0.5, 1.0)

    rec = {
        "buffer_id": buffer_id,
        "estimated_ionic_strength_mM": I_mM,
        "estimated_conductivity_mScm": kappa,
        "recommended_target_ionic_strength_mM": target_I,
        "recommended_target_conductivity_mScm": target_kappa,
        "recommended_df_time_h": 10.0,
        "recommended_headroom_fraction": 0.2,
        "recommended_nd_max": 8.0,
        "recommended_buffer_multiple_max": 2.5,
        "recommended_area_max_m2": None,
        "recommended_flags": {
            "use_planner": True,
            "auto_plan": True,
            "apply_flux_derate": False,
        },
        "overrides_stub": {
            "dsp03": {
                "buffers": {
                    "df": {
                        "use_planner": True,
                        "auto_plan": True,
                        "target_ionic_strength_mM": target_I,
                        "df_time_h_target": 10.0,
                        "nd_max": 8.0,
                        "buffer_multiple_max": 2.5,
                        "area_max_m2": None,
                        "headroom_fraction": 0.2,
                        "cost_from_registry": True,
                        "cost_buffer_id": buffer_id,
                    }
                }
            }
        },
    }
    return rec
