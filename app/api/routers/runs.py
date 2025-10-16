from fastapi import APIRouter
from pydantic import BaseModel
from ..models.scenario import Scenario
from ..engine.runner import run_deterministic
from ..engine.storage_fs import save_results
import uuid
import tempfile
import yaml
from migration.front_end import build_front_end_section

router = APIRouter()


class RunRequest(BaseModel):
    scenario: Scenario
    analyses: list[str] = ["deterministic"]


@router.post("")
def create_run(req: RunRequest):
    run_id = uuid.uuid4().hex[:8]
    results = run_deterministic(req.scenario)
    save_results(req.scenario.name, run_id, results)
    return {"run_id": run_id, "summary": results["kpis"]}


class FrontEndRunRequest(BaseModel):
    baseline_overrides: dict = {}
    mode: str = "baseline"


@router.post("/front_end")
def run_front_end(req: FrontEndRunRequest):
    # Materialize overrides to a temp YAML to reuse the existing front_end loader path
    with tempfile.NamedTemporaryFile("w+", suffix=".yaml", delete=False) as f:
        yaml.safe_dump(req.baseline_overrides, f)
        path = f.name

    section = build_front_end_section(
        None,
        mode=req.mode,
        baseline_config=path,
    )
    section.system.simulate()

    # Echo back any UI topology hints for transparency (Phase 1)
    ui_topology = None
    try:
        ui_topology = req.baseline_overrides.get('ui_topology')
    except Exception:
        ui_topology = None

    return {
        "cost_per_kg_usd": section.cost_per_kg_usd,
        "materials_cost_per_batch_usd": section.materials_cost_per_batch_usd,
        "materials_cost_per_kg_usd": section.materials_cost_per_kg_usd,
        "material_cost_breakdown": section.material_cost_breakdown,
        "dsp03_notes": getattr(section.dsp03_units[0].plan, "notes", []) if section.dsp03_units else [],
        "ui_topology": ui_topology,
    }
