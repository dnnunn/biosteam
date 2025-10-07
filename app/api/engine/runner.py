from datetime import datetime
from ..models.scenario import Scenario
from .builder import build_system


def run_deterministic(scenario: Scenario) -> dict:
    build = build_system(scenario)
    # TODO: call system.simulate(); TEA; compile KPIs
    results = {
        "scenario": scenario.name,
        "timestamp": datetime.utcnow().isoformat(),
        "kpis": {
            "cog_per_kg": None,
            "annual_throughput_kg": None,
            "overall_yield": None,
        },
        "engine": {
            "biosteam_version": "tbd",
            "thermosteam_version": "tbd",
            "git_hash": "tbd",
        },
    }
    return results
