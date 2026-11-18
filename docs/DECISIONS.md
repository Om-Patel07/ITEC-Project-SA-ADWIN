# Design decisions

From "Research findings that change the design" in the plan. Add a row for each new decision.

| # | Finding | Why it matters | Decision |
|---|---|---|---|
| F1 | River ADWIN checks for change only every `clock` points (default 32). | At 5-min data that is up to 160 min between checks; the latency target is impossible. | `clock=1` for SA-ADWIN and Vanilla ADWIN. Report the setting. |
| F2 | ADWIN's bound assumes inputs in [0, 1] (pysad PR #504). | Raw speed and residuals differ in scale, so the same delta means different sensitivity. | Map every ADWIN input to [0, 1] with fixed bounds from calibration weeks, then clip. Same rule for both ADWINs. |
| F3 | ADWIN is two-sided: fires on any mean change. | Alerts on incident recovery and speed-ups, doubling false alerts. | Direction filter (newer window slower) + cooldown, applied identically to all 4 methods in post-processing. |
| F4 | Holt-Winters keeps learning during an incident. | Incident is absorbed; residual shrinks and next day's forecast is wrong. | If residual > k sd, update HW with forecast/clipped value. Test as an ablation. |
| F5 | River 0.26.1 HoltWinters additive bug (issue #2077); waits max(2, m) values before starting. | Additive HW from River gives wrong forecasts. | Own HW class (~60 lines, O(1) per update), unit-tested vs statsmodels. |
| F6 | PeMS needs an account (1-2 business days); programmatic download disallowed. | Data could block Week 1. | Register now; download by hand. Fallback: PEMS-BAY (DCRNN repo, 325 sensors, 5-min, Jan-May 2017). |

Notes: traffic has daily (288) and weekly (2016) cycles; test both. Avoid METR-LA (~8% missing stored as zeros).
