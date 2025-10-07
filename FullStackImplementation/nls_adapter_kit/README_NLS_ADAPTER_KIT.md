# NLS Adapter Kit — Use Your Existing YAML Specs

You already have YAMLs derived from the BD Module Specs—perfect. This kit plugs Natural‑Language commands
into your *existing* YAMLs without changing their structure. Configure a few field names (if needed),
build an ontology, validate coverage, and you’re off.

## Files
- `nls_config.yaml` — map your YAML field names to the adapter's expected keys.
- `tools/build_ontology.py` — emits `ontology.json` from your YAMLs (unit & param synonyms).
- `tools/validate_specs.py` — quick coverage report (missing synonyms, collisions).
- `tools/try_nls.py` — run a command against a scenario JSON and see the patched output.

## Quick Start
1. Put your existing spec YAMLs under `app/units/specs/` (or another folder).
2. Check `nls_config.yaml` matches your schema (defaults: `template`, `synonyms`, `parameters[].key`, `parameters[].synonyms`).

3. Build the ontology:

   ```bash

   python tools/build_ontology.py --spec-dir app/units/specs --config nls_config.yaml --out ontology.json

   ```

4. Validate coverage (helpful before demos):

   ```bash

   python tools/validate_specs.py --spec-dir app/units/specs --config nls_config.yaml

   ```

5. Smoke test a command vs a scenario JSON:

   ```bash

   python tools/try_nls.py --spec-dir app/units/specs --scenario scenarios/OPN_demo.json --cmd "replace aex membrane with chitosan capture"

   ```

## Integrating with the API

If you’re using the **dynamic-ontology NLS router** I delivered, it already loads specs directly

from `app/units/specs`. You don’t need `ontology.json` at runtime—`/nls/help` will show what it discovered.

The builder scripts here are handy for CI and offline sanity checks.



## Tips for Better UX

- Add a few *friendly* synonyms per unit (e.g., "anion exchange", "AEX mem").

- Add short param aliases users will actually type ("pH", "flux", "area").

- Avoid synonym collisions: `validate_specs.py` will flag them.

