from pathlib import Path
import json

ROOT = Path("scenarios").resolve()


def save_results(scenario_name: str, run_id: str, results: dict) -> Path:
    outdir = ROOT / scenario_name / "results"
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{run_id}.json"
    path.write_text(json.dumps(results, indent=2))
    return path
