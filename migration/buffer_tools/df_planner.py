from __future__ import annotations

from dataclasses import dataclass


def compute_nd_from_ionic_strength(initial_mM: float | None, target_mM: float | None) -> float:
    """Compute diafiltration diavolumes ND from ionic strength reduction.

    Uses ND ≈ ln(I_in / I_target). Returns 0 when inputs are invalid or target >= initial.
    """
    try:
        I_in = float(initial_mM or 0.0)
        I_t = float(target_mM or 0.0)
    except (TypeError, ValueError):
        return 0.0
    if I_in <= 0.0 or I_t <= 0.0 or I_t >= I_in:
        return 0.0
    import math

    return max(math.log(I_in / I_t), 0.0)


@dataclass(frozen=True)
class DFPlan:
    nd: float
    buffer_volume_m3: float
    required_area_m2: float
    installed_area_m2: float
    df_time_h: float


def plan_df_cycle(
    *,
    feed_volume_m3: float,
    preuf_vrr: float,
    nd: float,
    flux_lmh: float,
    df_time_h: float,
    area_headroom_fraction: float = 0.2,
) -> DFPlan:
    """Return a DF plan with volumes and area sizing.

    - `feed_volume_m3`: incoming pool volume before pre-UF
    - `preuf_vrr`: volume reduction ratio in pre-UF (>=1)
    - `nd`: diafiltration diavolumes to run at constant volume (>=0)
    - `flux_lmh`: membrane flux [L/m2/h]
    - `df_time_h`: target DF time window [h]
    - `area_headroom_fraction`: multiplicative headroom added to required area
    """
    vrr = max(preuf_vrr, 1.0)
    nd = max(nd, 0.0)
    flux_m3_m2_h = max(flux_lmh, 0.0) / 1_000.0
    volume_preuf_m3 = max(feed_volume_m3 / vrr, 0.0)
    df_buffer_m3 = nd * volume_preuf_m3
    required_area_m2 = 0.0
    if flux_m3_m2_h > 0.0 and df_time_h > 0.0:
        required_area_m2 = df_buffer_m3 / (flux_m3_m2_h * df_time_h)
    installed_area_m2 = required_area_m2 * (1.0 + max(area_headroom_fraction, 0.0))
    return DFPlan(
        nd=nd,
        buffer_volume_m3=df_buffer_m3,
        required_area_m2=required_area_m2,
        installed_area_m2=installed_area_m2,
        df_time_h=max(df_time_h, 0.0),
    )

