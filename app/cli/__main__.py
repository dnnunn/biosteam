import argparse
import json
import yaml
from pathlib import Path
from app.api.models.scenario import Scenario
from app.api.engine.runner import run_deterministic


def main():
    p = argparse.ArgumentParser()
    p.add_argument("scenario", type=Path)
    p.add_argument("--out", type=Path, default=Path("results.json"))
    args = p.parse_args()
    sc = Scenario.model_validate(yaml.safe_load(args.scenario.read_text()))
    res = run_deterministic(sc)
    args.out.write_text(json.dumps(res, indent=2))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
