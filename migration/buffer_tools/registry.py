from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .buffers import BufferSpec, BufferComponent, ionic_strength_mM, estimate_conductivity_mScm


@dataclass(frozen=True)
class BufferRecord:
    id: str
    spec: BufferSpec


def _to_spec(entry: dict) -> Optional[BufferRecord]:
    try:
        bid = str(entry["id"])  # raises if missing
    except Exception:
        return None
    spec = BufferSpec.from_mapping(entry)
    if spec is None:
        return None
    return BufferRecord(id=bid, spec=spec)


def load_registry(path: Path | str = Path("migration/data_sources/buffers.json")) -> dict[str, BufferRecord]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    registry: dict[str, BufferRecord] = {}
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            rec = _to_spec(item)
            if rec is not None:
                registry[rec.id] = rec
    return registry


def get_buffer_spec(buffer_id: str, registry: dict[str, BufferRecord] | None = None) -> Optional[BufferSpec]:
    reg = registry or load_registry()
    rec = reg.get(str(buffer_id)) if reg else None
    return rec.spec if rec else None


def infer_properties(buffer_id: str) -> tuple[float, float]:
    """Return ionic strength (mM) and estimated conductivity (mS/cm) for a buffer ID.

    Returns (I_mM, kappa_mScm). Unknown IDs yield (0.0, 0.0).
    """
    spec = get_buffer_spec(buffer_id)
    if spec is None:
        return 0.0, 0.0
    I = ionic_strength_mM(spec)
    kappa = estimate_conductivity_mScm(spec)
    return I, kappa

