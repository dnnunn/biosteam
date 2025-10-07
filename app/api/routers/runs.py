from fastapi import APIRouter
from pydantic import BaseModel
from ..models.scenario import Scenario
from ..engine.runner import run_deterministic
from ..engine.storage_fs import save_results
import uuid

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
