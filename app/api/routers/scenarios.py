from fastapi import APIRouter
from ..models.scenario import Scenario
from pathlib import Path
import yaml

router = APIRouter()
ROOT = Path("scenarios").resolve()


@router.post("")
def upsert_scenario(scenario: Scenario):
    d = ROOT / scenario.name
    d.mkdir(parents=True, exist_ok=True)
    (d / "scenario.yaml").write_text(yaml.safe_dump(scenario.model_dump(by_alias=True)))
    return {"status": "ok", "path": str(d)}
