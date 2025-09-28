# OPN-focused tests

Place BioSTEAM/Osteopontin migration regression tests here. Pytest is configured to only pick up `test_opn_*.py` files under this directory.

## Refreshing the baseline fixture

Run the exporter whenever the Excel baseline changes:

```bash
conda activate /Users/davidnunn/Desktop/Apps/Biosteam/.conda-envs/biosteam310
python -m migration.scripts.export_baseline_metrics --workbook BaselineModel.xlsx
```

This writes `tests/opn/baseline_metrics.json`, which regression tests can consume.
