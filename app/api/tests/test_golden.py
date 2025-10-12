import pytest

from ..models.scenario import Scenario
from ..engine.runner import run_deterministic


def test_runs():
    sc = Scenario(
        name="OPN_demo",
        version="0.1",
        thermo_package=None,
        units=[{"template": "ProdFermenter_v2", "id": "prod1", "overrides": {}}],
        streams=[],
        assumptions={},
        uncertainty={},
    )
    out = run_deterministic(sc)
    kpis = out["kpis"]
    assert kpis["overall_yield"] == pytest.approx(6.2208, rel=1e-3)
    assert kpis["annual_throughput_kg"] == pytest.approx(2_520_000.0, rel=1e-3)
    assert kpis["cog_per_kg"] == pytest.approx(0.0, abs=1e-9)

    mass = out["mass_balance"]
    assert mass["final_product_kg_per_hr"] == pytest.approx(315.0, rel=1e-6)
    assert mass["feed_glucose_kg_per_hr"] == pytest.approx(50.636574074074076, rel=1e-6)

    metadata = out["units"]["prod1"]
    assert metadata["module"] == "USP00"
    assert metadata["target_product_mass_kg"] == pytest.approx(350.0, rel=1e-6)


def test_full_pipeline_runs_to_spray_dryer():
    sc = Scenario(
        name="OPN_full_demo",
        version="0.1",
        thermo_package=None,
        units=[
            {"template": "ProdFermenter_v2", "id": "fer", "overrides": {}},
            {"template": "MF_Polishing_v1", "id": "mf", "overrides": {}},
            {"template": "UFDF_v1", "id": "ufdf", "overrides": {}},
            {"template": "PreDry_TFF_v1", "id": "predry", "overrides": {}},
            {"template": "SprayDry_v1", "id": "dry", "overrides": {}},
        ],
        streams=[],
        assumptions={},
        uncertainty={},
    )
    out = run_deterministic(sc)

    mass = out["mass_balance"]
    assert mass["final_product_kg_per_hr"] == pytest.approx(296.2575, rel=1e-6)
    assert mass["feed_glucose_kg_per_hr"] == pytest.approx(50.636574074074076, rel=1e-6)

    units = out["units"]
    assert units["mf"]["product_out_kg"] == pytest.approx(311.85, rel=1e-6)
    assert units["ufdf"]["product_out_kg"] == pytest.approx(296.2575, rel=1e-6)
    assert units["dry"]["module"] == "DSP05"
