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
    assert "kpis" in out
