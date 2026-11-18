"""S3: inject synthetic incidents into a split and write the ground-truth labels.

Speed is multiplied by (1 - severity) during the incident, then ramps linearly
back to normal over `recovery_steps`. Half the incidents start in weekday peaks
(6-10 AM, 3-7 PM), and incidents at one station are at least `min_gap_hours` apart.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from sa_adwin.contracts import LABEL_COLUMNS, STEP_MINUTES

PEAK_HOURS = [(6, 10), (15, 19)]


def is_peak(ts: pd.DatetimeIndex) -> np.ndarray:
    hour = ts.hour + ts.minute / 60
    in_peak = np.zeros(len(ts), dtype=bool)
    for lo, hi in PEAK_HOURS:
        in_peak |= (hour >= lo) & (hour < hi)
    return in_peak & (ts.dayofweek < 5)


def profile(n_steps: int, severity: float, onset_type: str, recovery_steps: int) -> np.ndarray:
    """Multiplicative speed factor for each affected step (incident, then recovery)."""
    i = np.arange(n_steps)
    depth = np.ones(n_steps) if onset_type == "sudden" else np.minimum(1.0, (i + 1) / 3)
    recovery = 1 - (np.arange(recovery_steps) + 1) / (recovery_steps + 1)
    return 1 - severity * np.concatenate([depth, recovery])


def inject(
    long: pd.DataFrame, cfg: dict, seed: int, start: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (modified copy of `long` with an `injected` column, labels frame)."""
    rng = np.random.default_rng(seed)
    out = long.sort_values(["station", "ts"]).reset_index(drop=True)
    out["injected"] = False
    speed = out["speed"].to_numpy(dtype=float).copy()
    labels = []
    t0 = pd.Timestamp(start)
    min_gap = pd.Timedelta(hours=cfg["min_gap_hours"])

    for station, rows in out.groupby("station").indices.items():
        ts = pd.DatetimeIndex(out["ts"].to_numpy()[rows])
        ok = ~np.isnan(speed[rows])
        peak = is_peak(ts)
        week = (ts - t0) // pd.Timedelta(weeks=1)
        chosen: list[pd.Timestamp] = []
        for w in np.unique(week):
            n = cfg["per_station_week"]
            n_peak = int(round(n * cfg["peak_fraction"]))
            for want_peak in [True] * n_peak + [False] * (n - n_peak):
                dur = int(rng.choice(cfg["durations_min"]))
                sev = float(rng.choice(cfg["severities"]))
                onset_type = str(rng.choice(cfg["onset_types"]))
                f = profile(dur // STEP_MINUTES, sev, onset_type, cfg["recovery_steps"])
                span = len(f)
                cand = [
                    i for i in np.flatnonzero((week == w) & (peak == want_peak))
                    if i + span <= len(rows) and week[i + span - 1] == w and ok[i : i + span].all()
                    and all(abs(ts[i] - c) >= min_gap for c in chosen)
                ]  # fmt: skip
                if not cand:
                    continue
                i = int(rng.choice(cand))
                idx = rows[i : i + span]
                speed[idx] *= f
                out.loc[idx, "injected"] = True
                chosen.append(ts[i])
                labels.append({
                    "station": station, "onset": ts[i],
                    "end": ts[i] + pd.Timedelta(minutes=dur), "severity": sev,
                    "onset_type": onset_type, "peak": want_peak,
                })  # fmt: skip
    out["speed"] = speed
    labels_df = pd.DataFrame(labels, columns=LABEL_COLUMNS).sort_values(["station", "onset"])
    return out, labels_df.reset_index(drop=True)
