# tools/try_nls.py
"""
Try a natural-language command against a scenario JSON using your existing YAML specs.
Usage:
  python tools/try_nls.py --spec-dir app/units/specs --config nls_config.yaml --scenario scenarios/demo.json --cmd "replace aex membrane with chitosan capture"
"""
import argparse, json, jsonpatch
from pathlib import Path
from app.api.models.scenario import Scenario
from app.api.nls.ontology_loader import load_from_specs
from app.api.nls.parser import parse
from app.api.nls.editor import apply as build_patch

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--spec-dir", required=True)
    p.add_argument("--config", default="nls_config.yaml")
    p.add_argument("--scenario", required=True)
    p.add_argument("--cmd", required=True)
    args = p.parse_args()

    onto = load_from_specs(args.spec_dir)
    sc = Scenario.model_validate(json.loads(Path(args.scenario).read_text()))
    parsed = parse(args.cmd, onto)
    ops = build_patch(sc, parsed)
    data = jsonpatch.JsonPatch(ops).apply(sc.model_dump(by_alias=True), in_place=False)
    print(json.dumps({"parsed": parsed.__dict__, "patch": ops, "scenario_after": data}, indent=2))

if __name__ == "__main__":
    main()
