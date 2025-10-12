from __future__ import annotations

"""Compute ND and membrane area for DSP03 DF from buffer targets.

Usage examples:
  python -m migration.scripts.compute_df_plan \
    --feed-volume-m3 70 --vrr 3 --initial-I-mM 375 --target-I-mM 5 \
    --flux-lmh 90 --df-time-h 10 --headroom 0.2

  python -m migration.scripts.compute_df_plan \
    --feed-volume-m3 70 --vrr 3 --initial-kappa 45 --target-kappa 5 \
    --flux-lmh 90 --df-time-h 10 --headroom 0.2 --viscosity-mPa-s 5 --temp-C 25
"""

import argparse

from migration.buffer_tools import (
    compute_nd_from_ionic_strength,
    plan_df_cycle,
    water_viscosity_mPa_s,
    relative_viscosity,
    apply_viscosity_flux_derate,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--feed-volume-m3", type=float, required=True)
    p.add_argument("--vrr", type=float, required=True, help="Pre-UF volume reduction ratio (>=1)")
    p.add_argument("--initial-I-mM", type=float)
    p.add_argument("--target-I-mM", type=float)
    p.add_argument("--initial-kappa", type=float, help="Initial conductivity [mS/cm]")
    p.add_argument("--target-kappa", type=float, help="Target conductivity [mS/cm]")
    p.add_argument("--flux-lmh", type=float, required=True)
    p.add_argument("--df-time-h", type=float, required=True)
    p.add_argument("--headroom", type=float, default=0.2)
    p.add_argument("--viscosity-mPa-s", type=float)
    p.add_argument("--temp-C", type=float, default=25.0)
    return p.parse_args()


def main() -> None:
    a = parse_args()
    # Compute ND
    nd = 0.0
    if a.initial_I_mM and a.target_I_mM and a.initial_I_mM > a.target_I_mM:
        nd = compute_nd_from_ionic_strength(a.initial_I_mM, a.target_I_mM)
    elif a.initial_kappa and a.target_kappa and a.initial_kappa > a.target_kappa:
        import math

        nd = max(math.log(a.initial_kappa / a.target_kappa), 0.0)

    flux = float(a.flux_lmh)
    if a.viscosity_mPa_s and a.viscosity_mPa_s > 0.0:
        mu_w = water_viscosity_mPa_s(a.temp_C)
        rv = relative_viscosity(a.viscosity_mPa_s, mu_w)
        flux = apply_viscosity_flux_derate(flux, rv)

    plan = plan_df_cycle(
        feed_volume_m3=a.feed_volume_m3,
        preuf_vrr=a.vrr,
        nd=nd,
        flux_lmh=flux,
        df_time_h=a.df_time_h,
        area_headroom_fraction=a.headroom,
    )

    print(
        "ND={:.3f} | Buffer={:.2f} m3 | Area={:.1f} m2 (req) / {:.1f} m2 (inst) | tDF={:.2f} h | Flux={:.1f} LMH".format(
            plan.nd,
            plan.buffer_volume_m3,
            plan.required_area_m2,
            plan.installed_area_m2,
            plan.df_time_h,
            flux,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()

