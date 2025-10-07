# /app/api/nls/ontology_loader.py
from __future__ import annotations
from pathlib import Path
import yaml
from typing import Dict, Tuple

class Ontology:
    def __init__(self, unit_map: Dict[str,str], param_map: Dict[str,str]):
        self.unit_map = {k.lower(): v for k,v in unit_map.items()}
        self.param_map = {k: v for k,v in param_map.items()}
    def resolve_unit(self, name: str) -> str:
        return self.unit_map.get(name.strip().lower(), name)
    def resolve_param(self, name: str) -> str:
        return self.param_map.get(name.strip(), name)

def load_from_specs(spec_dir: str | Path) -> Ontology:
    spec_dir = Path(spec_dir)
    unit_map = {}
    param_map = {}
    for path in sorted(spec_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text()) or {}
        canon = data.get("template")
        for s in data.get("synonyms", []):
            unit_map[s] = canon
        # allow canonical name to map to itself
        if canon:
            unit_map[canon] = canon
        # parameters
        for p in data.get("parameters", []):
            canon_p = p.get("key")
            for s in p.get("synonyms", []):
                param_map[s] = canon_p
            if canon_p:
                param_map[canon_p] = canon_p
    return Ontology(unit_map, param_map)
