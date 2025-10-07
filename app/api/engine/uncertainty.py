from ..models.scenario import Scenario


def run_sobol(scenario: Scenario, n: int = 512) -> dict:
    # Placeholder; wire SALib in a later PR
    return {"samples": n, "results": []}
