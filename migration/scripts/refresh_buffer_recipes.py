from __future__ import annotations

"""
Manual curation script stub to refresh buffer recipes from allowed sources.

Usage (manual):
  python -m migration.scripts.refresh_buffer_recipes --dry-run

Notes:
- This script is intentionally a stub: runtime networking is not performed.
- Curated outputs must be written to migration/data_sources/buffers.json with
  provenance (source_url, publisher, license, retrieved_at, checksum).
- CI and tests should consume only the checked-in snapshot for determinism.
"""

import argparse
import hashlib
import json
from pathlib import Path


def _sha256_text(text: str) -> str:
    h = hashlib.sha256()
    h.update(text.encode("utf-8"))
    return h.hexdigest()


def _validate_snapshot(data: object) -> list[str]:
    errs: list[str] = []
    if not isinstance(data, list):
        return ["Top-level must be a list"]
    for idx, entry in enumerate(data):
        if not isinstance(entry, dict):
            errs.append(f"Entry {idx}: not an object")
            continue
        for key in ("id", "components"):
            if key not in entry:
                errs.append(f"Entry {idx}: missing '{key}'")
        comps = entry.get("components")
        if isinstance(comps, list):
            for j, comp in enumerate(comps):
                if not isinstance(comp, dict):
                    errs.append(f"Entry {idx} comp {j}: not an object")
                    continue
                for ck in ("name", "concentration_mM", "charge_z"):
                    if ck not in comp:
                        errs.append(f"Entry {idx} comp {j}: missing '{ck}'")
    return errs


def parse_args() -> argparse.Namespace:  # pragma: no cover
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true", help="Print plan without writing files")
    p.add_argument("--validate", action="store_true", help="Validate snapshot schema")
    p.add_argument("--update-checksums", action="store_true", help="Write sha256 checksum into provenance for each entry")
    p.add_argument("--diff", type=Path, help="Compare current buffers.json against another JSON file (ID-level diff)")
    return p.parse_args()


def main() -> None:  # pragma: no cover
    args = parse_args()
    ds = Path("migration/data_sources/buffers.json")
    allow = Path("migration/data_sources/allowlist.json")
    print("Allowed sources:", allow.read_text(encoding="utf-8"))
    raw = ds.read_text(encoding="utf-8")
    print("Current buffer snapshot:")
    print(raw)
    data = None
    try:
        data = json.loads(raw)
    except Exception as e:
        print("ERROR: invalid JSON:", e)
    if args.validate and data is not None:
        errs = _validate_snapshot(data)
        if errs:
            print("VALIDATION ERRORS:")
            for err in errs:
                print(" -", err)
        else:
            print("Snapshot schema: OK")
    if args.diff and data is not None:
        try:
            other = json.loads(Path(args.diff).read_text(encoding="utf-8"))
        except Exception as e:  # pragma: no cover
            print("ERROR reading diff target:", e)
            other = None
        if isinstance(other, list):
            def _index(lst):
                m = {}
                for it in lst:
                    if isinstance(it, dict) and "id" in it:
                        m[str(it["id"])]=it
                return m
            a = _index(data)
            b = _index(other)
            added = sorted(set(b.keys())-set(a.keys()))
            removed = sorted(set(a.keys())-set(b.keys()))
            common = sorted(set(a.keys()) & set(b.keys()))
            print("Added IDs:", added)
            print("Removed IDs:", removed)
            print("Changed IDs:")
            for k in common:
                ea, eb = a[k], b[k]
                diffs = []
                for fld in ("components","reagents","pH","temperature_C"):
                    if ea.get(fld) != eb.get(fld):
                        diffs.append(fld)
                if diffs:
                    print(f" - {k}: fields changed: {', '.join(diffs)}")
        else:
            print("No diff computed; invalid target file.")

    if args.update_checksums and data is not None:
        changed = False
        for entry in data:
            if not isinstance(entry, dict):
                continue
            prov = entry.get("provenance")
            if not isinstance(prov, dict):
                continue
            content = json.dumps({k: entry.get(k) for k in ("id", "components", "pH", "temperature_C")}, sort_keys=True)
            checksum = _sha256_text(content)
            if prov.get("checksum") != checksum:
                prov["checksum"] = checksum
                changed = True
        if changed and not args.dry_run:
            ds.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print("Updated checksums written to", ds)
        elif changed:
            print("Checksums would be updated (dry-run)")


if __name__ == "__main__":  # pragma: no cover
    main()
