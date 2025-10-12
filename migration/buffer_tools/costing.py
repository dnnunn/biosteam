from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Optional


@dataclass(frozen=True)
class Reagent:
    name: str
    molar_mass_g_per_mol: float
    price_per_kg_usd: float


def load_reagent_catalog(path: Path | str = Path("migration/data_sources/reagent_prices.json")) -> dict[str, Reagent]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: dict[str, Reagent] = {}
    if isinstance(data, list):
        for item in data:
            try:
                name = str(item["name"]).strip()
                mm = float(item["molar_mass_g_per_mol"])  # g/mol
                price = float(item["price_per_kg_usd"])    # USD/kg
            except Exception:
                continue
            out[name.lower()] = Reagent(name=name, molar_mass_g_per_mol=mm, price_per_kg_usd=price)
    return out


def _cost_for_reagent(concentration_mM: float, reagent: Reagent) -> float:
    """Return cost contribution [USD/m3] for a reagent at given mM."""
    # mM → mol/L → g/L → kg/m3
    mol_per_L = max(float(concentration_mM), 0.0) / 1000.0
    g_per_L = mol_per_L * reagent.molar_mass_g_per_mol
    kg_per_m3 = g_per_L  # 1 g/L == 1 kg/m3
    return kg_per_m3 * reagent.price_per_kg_usd


def estimate_cost_per_m3_from_reagents(
    reagents: Iterable[Mapping[str, object]],
    catalog: Mapping[str, Reagent] | None = None,
) -> float:
    """Estimate buffer cost [USD/m3] from a reagents list in a buffer spec.

    Each entry must include: {"name": str, "concentration_mM": float}.
    """
    cat = dict(catalog) if catalog is not None else load_reagent_catalog()
    total = 0.0
    for entry in reagents:
        if not isinstance(entry, Mapping):
            continue
        name = str(entry.get("name", "")).strip().lower()
        try:
            conc = float(entry.get("concentration_mM"))
        except Exception:
            conc = 0.0
        if conc <= 0.0:
            continue
        reagent = cat.get(name)
        if reagent is None:
            continue
        total += _cost_for_reagent(conc, reagent)
    return total


def estimate_cost_per_m3_for_buffer_id(buffer_id: str, buffers_path: Path | str = Path("migration/data_sources/buffers.json"), catalog_path: Path | str = Path("migration/data_sources/reagent_prices.json")) -> Optional[float]:
    """Return estimated cost per m3 [USD/m3] for a buffer ID if reagents are specified.

    Falls back to None when missing.
    """
    bp = Path(buffers_path)
    cat = load_reagent_catalog(catalog_path)
    try:
        data = json.loads(bp.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, list):
        return None
    for entry in data:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("id")) == str(buffer_id):
            reagents = entry.get("reagents")
            if isinstance(reagents, list):
                return estimate_cost_per_m3_from_reagents(reagents, cat)
            return None
    return None

