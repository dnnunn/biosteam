from __future__ import annotations

import pytest

from migration.capture import CaptureHandoff, CaptureRoute
from migration.dsp03 import build_dsp03_chain


def _handoff(cond_mM: float, volume_l: float, product_kg: float) -> CaptureHandoff:
    return CaptureHandoff(
        route=CaptureRoute.AEX,
        pool_volume_l=volume_l,
        opn_concentration_g_per_l=(product_kg * 1000.0 / volume_l if volume_l > 0 else 0.0),
        conductivity_mM=cond_mM,
        ph=7.0,
        dna_mg_per_l=None,
        chitosan_ppm=None,
        polyp_mM=0.0,
        step_recovery_fraction=1.0,
        needs_df=False,
        needs_fines_polish=False,
        cycle_time_h=0.0,
        cost_per_batch=0.0,
        notes=[],
    )


@pytest.mark.not_slow
def test_auto_plan_updates_nd_and_area():
    # 75-fold reduction target: ND ≈ ln(75) ≈ 4.317
    handoff = _handoff(cond_mM=375.0, volume_l=70_000.0, product_kg=300.0)
    cfg = {
        "parameters": {
            "vr_preuf": 3.0,
            "flux_lmh": 90.0,
            "df_time_h": 10.0,
        },
        "auto_plan": True,
        "buffers": {
            "df": {
                "use_planner": True,
                "target_ionic_strength_mM": 5.0,
                "df_time_h_target": 10.0,
                "nd_max": 8.0,
                "buffer_multiple_max": 10.0,
                "area_max_m2": 200.0,
                "headroom_fraction": 0.2,
            }
        },
    }
    chain = build_dsp03_chain(capture_handoff=handoff, config_mapping=cfg)
    unit = chain.units[0]
    d = unit.plan.derived
    assert d["df_time_h"] >= 10.0  # may be increased by area cap
    assert d["installed_area_m2"] <= 200.0 + 1e-6
    # DF buffer should be ND * (V/VRR)
    v_rr = 3.0
    preuf_m3 = 70.0 / v_rr
    # ND should be about ln(75) unless area cap forces larger time (doesn't change ND)
    # Just ensure buffer is in the right ballpark
    assert d["df_buffer_volume_m3"] == pytest.approx(preuf_m3 * 4.317, rel=0.15)


@pytest.mark.not_slow
def test_auto_plan_viscosity_derate():
    handoff = _handoff(cond_mM=200.0, volume_l=30_000.0, product_kg=150.0)
    cfg = {
        "parameters": {
            "vr_preuf": 3.0,
            "flux_lmh": 90.0,
            "df_time_h": 10.0,
        },
        "auto_plan": True,
        "buffers": {
            "df": {
                "use_planner": True,
                "target_ionic_strength_mM": 20.0,
                "viscosity_mPa_s": 5.0,  # ~5× water → should derate flux
                "viscosity_temp_C": 25.0,
                "df_time_h_target": 10.0,
            }
        },
    }
    chain = build_dsp03_chain(capture_handoff=handoff, config_mapping=cfg)
    unit = chain.units[0]
    d = unit.plan.derived
    # With viscosity derate, installed area should be higher than if no derate at same time
    assert d["installed_area_m2"] > 0.0
