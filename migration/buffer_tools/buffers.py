from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class BufferComponent:
    name: str
    concentration_mM: float
    charge_z: float


@dataclass(frozen=True)
class BufferSpec:
    components: tuple[BufferComponent, ...]
    pH: float | None = None
    temperature_C: float | None = None
    source: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, object] | None) -> "BufferSpec | None":
        if not isinstance(data, Mapping):
            return None
        comps_raw = data.get("components")
        if not isinstance(comps_raw, Iterable):
            return None
        components: list[BufferComponent] = []
        for item in comps_raw:
            if not isinstance(item, Mapping):
                continue
            try:
                name = str(item.get("name"))
                conc = float(item.get("concentration_mM"))
                charge = float(item.get("charge_z"))
            except (TypeError, ValueError):
                continue
            components.append(BufferComponent(name=name, concentration_mM=conc, charge_z=charge))
        if not components:
            return None
        return cls(
            components=tuple(components),
            pH=(float(data.get("pH")) if data.get("pH") is not None else None),
            temperature_C=(float(data.get("temperature_C")) if data.get("temperature_C") is not None else None),
            source=(str(data.get("source")) if data.get("source") is not None else None),
        )


def ionic_strength_mM(spec: BufferSpec | None) -> float:
    """Return ionic strength (mM) for the buffer spec using I = 0.5 * sum(ci * zi^2).

    - `ci` in mM, `zi` unitless charge. Output is mM (not mol/L).
    """
    if spec is None or not spec.components:
        return 0.0
    I_mM = 0.0
    for comp in spec.components:
        try:
            I_mM += float(comp.concentration_mM) * (float(comp.charge_z) ** 2)
        except (TypeError, ValueError):
            continue
    return 0.5 * I_mM


_LAMBDA0_SCM2_PER_MOL_25C: dict[str, float] = {
    # Common ions at 25 °C (approximate, infinite dilution)
    "h+": 349.65,
    "oh-": 198.5,
    "na+": 50.1,
    "k+": 73.5,
    "nh4+": 73.5,
    # Tris family (approximate, treat protonated tris similarly to other small organic cations)
    "tris+": 55.0,
    "trish+": 55.0,
    "tris-h+": 55.0,
    "tris": 0.0,  # unprotonated base is neutral and does not contribute
    "ca2+": 119.0,
    "mg2+": 106.0,
    "cl-": 76.3,
    "no3-": 71.5,
    "acetate-": 40.9,
    "hco3-": 44.5,
    "co3^2-": 69.0,
    "so4^2-": 160.0,
    # Phosphate species (rough approximations)
    "h2po4-": 33.5,
    "hpo4^2-": 50.0,
    "po4^3-": 40.0,
    # Citrate forms (very approximate)
    "citrate3-": 40.0,
    "hcitrate2-": 35.0,
    "hhcitrate-": 30.0,
}


_TEMP_COEFF_PER_C: dict[str, float] = {
    # Linear temperature coefficients (per °C) for conductivity scaling around 25 °C
    # Defaults ~2%/°C; ion-specific deviations are small at dilute solutions.
    "default": 0.02,
    "na+": 0.019,
    "k+": 0.019,
    "cl-": 0.020,
    "so4^2-": 0.020,
}


def estimate_conductivity_mScm(spec: BufferSpec | None) -> float:
    """Estimate conductivity (mS/cm) via sum of limiting molar conductivities.

    κ[mS/cm] ≈ Σ Λ⁰_i[S·cm²/mol] · c_i[mol/L]. This is a conservative estimate for
    dilute solutions at ~25 °C and ignores ion pairing/activity effects.
    """
    if spec is None or not spec.components:
        return 0.0
    total = 0.0
    for comp in spec.components:
        try:
            c_mol_l = float(comp.concentration_mM) / 1_000.0
        except (TypeError, ValueError):
            continue
        key = comp.name.strip().lower()
        lam = _LAMBDA0_SCM2_PER_MOL_25C.get(key)
        if lam is None:
            # Try common normalized keys
            key2 = key.replace(" ", "").replace("--", "-")
            lam = _LAMBDA0_SCM2_PER_MOL_25C.get(key2)
        if lam is None:
            continue
        total += lam * c_mol_l
    kappa_25 = max(total, 0.0)
    # Apply a simple linear temperature correction around 25 °C
    T = 25.0
    try:
        if spec.temperature_C is not None:
            T = float(spec.temperature_C)
    except (TypeError, ValueError):
        T = 25.0
    dT = T - 25.0
    alpha = _TEMP_COEFF_PER_C.get("default", 0.02)
    return max(kappa_25 * (1.0 + alpha * dT), 0.0)
