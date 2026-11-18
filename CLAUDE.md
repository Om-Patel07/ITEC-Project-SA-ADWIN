# SA-ADWIN — traffic alert-fatigue study (ITEC 5205)
Holt-Winters residual -> ADWIN, vs rolling Z-score, HW + static threshold, Vanilla ADWIN.
Plan: https://claude.ai/artifact/4ajcgVGSBYti6yWvtjEBRK · Progress: @docs/STATUS.md

## Commands
- Install (Python 3.11+): `pip install -e ".[dev]"`
- Data: see docs/DATA.md, then `python scripts/prepare_data.py --config configs/base.yaml`
- Tests: `pytest -q` (synthetic data, no PeMS needed)
- Lint: `ruff check src tests && ruff format src tests`
- Run: `python scripts/run_experiment.py --config configs/base.yaml`

## Layout (owner)
- `src/sa_adwin/contracts.py` shared types; changes need all 3 approvals
- `src/sa_adwin/data/` [Om] ingest, split, inject, stream replay
- `src/sa_adwin/detectors/` holt_winters, hw_threshold, sa_adwin [Jasmit]; zscore, adwin_vanilla [Utkarsh]
- `src/sa_adwin/eval/` postprocess, evaluate [Utkarsh]; profile [Om]
- `tests/fixtures.py` synthetic traffic with labelled incidents

## Rules
- Detectors implement `update(record) -> Signal | None`; never use future values.
- Direction filter + cooldown live only in eval/postprocess.py (same for all methods).
- Tune on week 3 only; never touch test weeks 4-6 when tuning.
- Every change needs a test that runs on tests/fixtures.py in under 5 s.
- Stay inside your own folder; PRs under ~300 lines; update docs/STATUS.md in the same PR.
- Read docs/DECISIONS.md before changing detector behaviour.
