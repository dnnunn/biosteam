# tools/build_ontology.py
"""
Build an ontology JSON from existing YAML specs using a flexible field mapping.
Usage:
  python tools/build_ontology.py --spec-dir app/units/specs --config nls_config.yaml --out ontology.json
"""
import argparse, json, sys
from pathlib import Path
import yaml

def load_config(path: Path) -> dict:
    data = yaml.safe_load(path.read_text())
    return data.get("fields", {})

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--spec-dir", required=True)
    p.add_argument("--config", default="nls_config.yaml")
    p.add_argument("--out", default="ontology.json")
    args = p.parse_args()

    fields = load_config(Path(args.config))
    unit_key = fields.get("unit_key", "template")
    unit_synonyms_key = fields.get("unit_synonyms", "synonyms")
    params_key = fields.get("params_key", "parameters")
    param_name_key = fields.get("param_name_key", "key")
    param_synonyms_key = fields.get("param_synonyms_key", "synonyms")

    spec_dir = Path(args.spec_dir)
    unit_map = {}
    param_map = {}

    for f in sorted(spec_dir.glob("*.yaml")):
        doc = yaml.safe_load(f.read_text()) or {}
        canon = doc.get(unit_key)
        if not canon:
            print(f"[WARN] {f.name}: missing '{unit_key}'", file=sys.stderr)
            continue
        # unit synonyms
        for s in doc.get(unit_synonyms_key, []) or []:
            unit_map[s.lower()] = canon
        unit_map[canon.lower()] = canon
        # params
        for pdoc in doc.get(params_key, []) or []:
            pname = pdoc.get(param_name_key)
            if not pname:
                print(f"[WARN] {f.name}: parameter missing '{param_name_key}'", file=sys.stderr)
                continue
            for s in pdoc.get(param_synonyms_key, []) or []:
                param_map[s] = pname
            param_map[pname] = pname

    ontology = {"unit_map": unit_map, "param_map": param_map}
    Path(args.out).write_text(json.dumps(ontology, indent=2))
    print(f"[OK] wrote {args.out} with {len(unit_map)} unit synonyms and {len(param_map)} param synonyms")

if __name__ == "__main__":
    main()
