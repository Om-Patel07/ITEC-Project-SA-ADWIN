# Status board

Plan: https://claude.ai/artifact/4ajcgVGSBYti6yWvtjEBRK · Updated: 2026-11-18
State: todo / doing / done. Update your row in the same PR as the change.

| Stage | Owner | Due | Done when | State |
|---|---|---|---|---|
| PeMS account + PEMS-BAY fallback | Om | Nov 18 | Account requested, PEMS-BAY downloaded (docs/DATA.md) | doing (PEMS-BAY done; PeMS account pending) |
| S0 Acquire | Om | Nov 24 | 6+ weeks, 20-40 mainline stations, one district | todo |
| S1 Clean + QC | Om | Nov 24 | Gaps <= 3 filled; < 90% observed dropped; QC table saved | done (PEMS-BAY: 325/325 kept, top 30 used) |
| S2 Split | Om | Nov 24 | Cal wk 1-2, val wk 3, test wk 4-6 fixed in config | done |
| S3 Inject | Om | Nov 24 | labels.csv; 10 random injections look plausible to all 3 | doing (labels written; plot check pending) |
| S4 Replay | Om | Nov 24 | Unit test: no detector can read a future value | done |
| S5 Holt-Winters (own class) | Jasmit | Nov 24 | Matches statsmodels on a fixed series (m=288, 2016) | todo |
| S5 Vanilla ADWIN + SA-ADWIN | Jasmit | Nov 24 | clock=1, [0,1] scaling, robust HW update | todo |
| S5 Z-score + HW threshold | Utkarsh | Nov 24 | Pass the shared interface test | todo |
| S6 Filter + S7 Evaluate | Utkarsh | Nov 24 | Same path for all 4; hand-checked on 3-incident toy stream | todo |
| Shared skeleton (contracts.py, fixtures, config) | Om | Nov 18 | Detector + Signal contract, synthetic fixtures | done (needs Jasmit + Utkarsh approval) |
| **Gate 1** | All | Tue Nov 24 | All 4 methods run on 1 station -> metrics CSV | todo |
| S8 Sweeps on validation week | Jasmit + Utkarsh | Dec 1 | Operating points chosen | todo |
| S8 Test runs (all stations x 5 seeds) | Om | Dec 1 | Parallelised; one command reproduces | todo |
| Trade-off curves + matched-recall table | Utkarsh | Dec 1 | Recall vs false alerts per station-day | todo |
| **Gate 2** | All | Tue Dec 1 | Headline table checked vs 5 success criteria | todo |
| Ablations, memory 1x/2x/4x, throughput | Jasmit | Dec 4 | Robust update, 288 vs 2016, clock 1 vs 32 | todo |
| Demo plot + README | Om | Dec 4 | One station, alerts from 4 methods | todo |
| **Code freeze** | All | Fri Dec 4 | No method changes after this | todo |
| S9 Report + slides | All | Dec 7 | Every number traces to a results file | todo |
| Submit | All | Tue Dec 8 | Wed Dec 9 is buffer | todo |

If Gate 1 slips, cut ablations, not the evaluation.
