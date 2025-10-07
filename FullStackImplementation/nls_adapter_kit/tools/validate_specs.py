# tools/validate_specs.py
"""
Validate coverage of your YAML specs:
  - list units missing synonyms
  - parameters missing synonyms
  - detect duplicate synonym collisions
Usage:
  python tools/validate_specs.py --spec-dir app/units/specs --config nls_config.yaml
"""
import argparse, sys
from pathlib import Path
import yaml
from collections import defaultdict

def load_config(path: Path) -> dict:
    data = yaml.safe_load(path.read_text())
    return data.get("fields", {})

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--spec-dir", required=True)
    p.add_argument("--config", default="nls_config.yaml")
    args = p.parse_args()

    fields = load_config(Path(args.config))
    unit_key = fields.get("unit_key", "template")
    unit_synonyms_key = fields.get("unit_synonyms", "synonyms")
    params_key = fields.get("params_key", "parameters")
    param_name_key = fields.get("param_name_key", "key")
    param_synonyms_key = fields.get("param_synonyms_key", "synonyms")

    spec_dir = Path(args.spec_dir)
    unit_synonyms_seen = defaultdict(list)
    param_synonyms_seen = defaultdict(list)
    issues = 0

    for f in sorted(spec_dir.glob("*.yaml")):
        doc = yaml.safe_load(f.read_text()) or {}
        canon = doc.get(unit_key)
        syns = doc.get(unit_synonyms_key, []) or []
        if not canon:
            print(f"[ERROR] {f.name}: missing '{unit_key}'", file=sys.stderr); issues += 1; continue
        if not syns:
            print(f"[WARN] {f.name}: unit '{canon}' has no synonyms", file=sys.stderr)
        for s in syns:
            unit_synonyms_seen[s.lower()].append(f.name)
        # params
        for pdoc in doc.get(params_key, []) or []:
            pname = pdoc.get(param_name_key)
            if not pname:
                print(f"[ERROR] {f.name}: parameter missing '{param_name_key}'", file=sys.stderr); issues += 1; continue
            psyns = pdoc.get(param_synonyms_key, []) or []
            if not psyns:
                print(f"[WARN] {f.name}: param '{pname}' has no synonyms", file=sys.stderr)
            for s in psyns:
                param_synonyms_seen[s].append(f.name)

    # collisions
    for syn, files in unit_synonyms_seen.items():
        if len(files) > 1:
            print(f"[COLLISION] unit synonym '{syn}' appears in: {', '.join(files)}", file=sys.stderr); issues += 1
    for syn, files in param_synonyms_seen.items():
        if len(files) > 1:
            print(f"[COLLISION] param synonym '{syn}' appears in: {', '.join(files)}", file=sys.stderr); issues += 1

    if issues:
        print(f"[SUMMARY] Detected {issues} issues (errors/collisions).", file=sys.stderr)
    else:
        print("[SUMMARY] Specs look good. Add more synonyms if UX needs them.")

if __name__ == "__main__":
    main()
