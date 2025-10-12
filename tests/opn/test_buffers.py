from __future__ import annotations

import math
import pytest

from migration.buffer_tools import (
    BufferComponent,
    BufferSpec,
    ionic_strength_mM,
    compute_nd_from_ionic_strength,
    plan_df_cycle,
)
from migration.buffer_tools.buffers import estimate_conductivity_mScm
from migration.buffer_tools import water_viscosity_mPa_s, relative_viscosity, apply_viscosity_flux_derate, glycerol_solution_viscosity_mPa_s


@pytest.mark.not_slow
def test_ionic_strength_simple_mix():
    # 100 mM NaCl → I = 0.5*(100*1^2 + 100*1^2) = 100 mM
    spec = BufferSpec(
        components=(
            BufferComponent(name="Na+", concentration_mM=100.0, charge_z=1),
            BufferComponent(name="Cl-", concentration_mM=100.0, charge_z=-1),
        )
    )
    I = ionic_strength_mM(spec)
    assert I == pytest.approx(100.0, rel=1e-6)


@pytest.mark.not_slow
def test_compute_nd_from_ionic_strength():
    # From 375 mM to 5 mM → ND ≈ ln(375/5) = ln(75)
    nd = compute_nd_from_ionic_strength(375.0, 5.0)
    assert nd == pytest.approx(math.log(75.0), rel=1e-6)
    # Guard rails: invalid/bad inputs → 0
    assert compute_nd_from_ionic_strength(None, 5.0) == 0.0
    assert compute_nd_from_ionic_strength(5.0, None) == 0.0
    assert compute_nd_from_ionic_strength(5.0, 10.0) == 0.0


@pytest.mark.not_slow
def test_plan_df_cycle_volumes_and_area():
    # 70 m3 feed, VRR=3, ND=5, flux=90 LMH, DF time=10 h
    plan = plan_df_cycle(
        feed_volume_m3=70.0,
        preuf_vrr=3.0,
        nd=5.0,
        flux_lmh=90.0,
        df_time_h=10.0,
        area_headroom_fraction=0.2,
    )
    # Pre-UF retentate = 70/3; buffer volume = ND*V_R
    assert plan.buffer_volume_m3 == pytest.approx(5.0 * (70.0 / 3.0), rel=1e-6)
    # Required area = buffer / (flux * time) with flux in m3/m2/h
    required = plan.buffer_volume_m3 / ((90.0 / 1000.0) * 10.0)
    assert plan.required_area_m2 == pytest.approx(required, rel=1e-6)
    assert plan.installed_area_m2 == pytest.approx(required * 1.2, rel=1e-6)


@pytest.mark.not_slow
def test_estimate_conductivity_nacl():
    # 100 mM NaCl → conductance ≈ (Λ0_Na + Λ0_Cl) * 0.1 ≈ 12.6 mS/cm
    spec = BufferSpec(
        components=(
            BufferComponent(name="Na+", concentration_mM=100.0, charge_z=1),
            BufferComponent(name="Cl-", concentration_mM=100.0, charge_z=-1),
        )
    )
    kappa = estimate_conductivity_mScm(spec)
    assert kappa == pytest.approx(12.6, rel=0.2)


@pytest.mark.not_slow
def test_temperature_correction_linear():
    spec25 = BufferSpec(
        components=(
            BufferComponent(name="Na+", concentration_mM=100.0, charge_z=1),
            BufferComponent(name="Cl-", concentration_mM=100.0, charge_z=-1),
        ),
        temperature_C=25.0,
    )
    spec35 = BufferSpec(
        components=spec25.components,
        temperature_C=35.0,
    )
    k25 = estimate_conductivity_mScm(spec25)
    k35 = estimate_conductivity_mScm(spec35)
    # Expect ~20% increase for +10 °C with alpha≈0.02/°C (allow 10% tol)
    assert k35 == pytest.approx(k25 * 1.2, rel=0.1)


@pytest.mark.not_slow
def test_water_viscosity_monotonic_with_temperature():
    mu10 = water_viscosity_mPa_s(10.0)
    mu25 = water_viscosity_mPa_s(25.0)
    mu40 = water_viscosity_mPa_s(40.0)
    assert mu10 > mu25 > mu40


@pytest.mark.not_slow
def test_viscosity_flux_derate():
    mu_w = water_viscosity_mPa_s(25.0)
    mu_sol = mu_w * 5.0
    rv = relative_viscosity(mu_sol, mu_w)
    f0 = 100.0
    f1 = apply_viscosity_flux_derate(f0, rv)
    assert f1 == pytest.approx(20.0, rel=1e-6)  # min fraction 0.2 cap kicks in
    f2 = apply_viscosity_flux_derate(f0, 2.0, min_fraction=0.1)
    assert f2 == pytest.approx(50.0, rel=1e-6)


@pytest.mark.not_slow
def test_glycerol_mixture_viscosity_reasonable():
    mu_w = water_viscosity_mPa_s(25.0)
    mu_mix_low = glycerol_solution_viscosity_mPa_s(0.1, 25.0)
    mu_mix_high = glycerol_solution_viscosity_mPa_s(0.6, 25.0)
    assert mu_mix_low > mu_w
    assert mu_mix_high > mu_mix_low
