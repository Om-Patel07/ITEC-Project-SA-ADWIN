# SA-ADWIN — traffic alert-fatigue study (ITEC 5205)

Does removing the expected rush-hour pattern with Holt-Winters before ADWIN cut false
alerts without missing real incidents? We compare **SA-ADWIN** (Holt-Winters residual ->
ADWIN) with rolling Z-score, Holt-Winters + static threshold, and Vanilla ADWIN on 5-minute
freeway speed data with injected incidents.

- Progress board: [docs/STATUS.md](docs/STATUS.md)
- Design decisions F1-F6: [docs/DECISIONS.md](docs/DECISIONS.md)
- Data download and data-use rules: [docs/DATA.md](docs/DATA.md)

## Setup (Python 3.11+)
```
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"      # macOS/Linux: .venv/bin/pip
```

## Commands
- Prepare data (S1-S3): `python scripts/prepare_data.py --config configs/base.yaml`
- Tests: `pytest -q` (synthetic data, no PeMS needed)
- Lint: `ruff check src tests && ruff format src tests`

## Layout and owners
- `src/sa_adwin/contracts.py` shared types; changes need all 3 approvals
- `src/sa_adwin/data/` [Om] ingest, split, inject, stream replay
- `src/sa_adwin/detectors/` holt_winters, hw_threshold, sa_adwin [Jasmit]; zscore, adwin_vanilla [Utkarsh]
- `src/sa_adwin/eval/` postprocess, evaluate [Utkarsh]; profile [Om]
- `tests/fixtures.py` synthetic traffic with labelled incidents

## Team rules
- Detectors implement `update(record) -> Signal | None`; never use future values.
- Direction filter + cooldown live only in `eval/postprocess.py` (same for all methods).
- Tune on week 3 only; never touch test weeks 4-6 when tuning.
- Every change needs a test that runs on `tests/fixtures.py` in under 5 s.
- Stay inside your own folder; PRs under ~300 lines; update docs/STATUS.md in the same PR.
- Read docs/DECISIONS.md before changing detector behaviour.
- Never commit data, results, or credentials (see docs/DATA.md).

## Data credits
Caltrans Performance Measurement System (PeMS), https://pems.dot.ca.gov.
PEMS-BAY from Li et al. 2018, "Diffusion Convolutional Recurrent Neural Network" (ICLR).
