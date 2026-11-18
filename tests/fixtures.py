"""Synthetic traffic with labelled incidents, so tests never need PeMS.

Speed has a daily cycle with weekday rush-hour slowdowns, plus noise.
Everything is seeded; building 3 stations x 6 weeks takes well under a second.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from sa_adwin.data.ingest import period

START = "2017-02-27"  # a Monday
INJECT_CFG = {
    "severities": [0.20, 0.35, 0.50],
    "durations_min": [15, 30, 60],
    "onset_types": ["sudden", "gradual"],
    "per_station_week": 2,
    "min_gap_hours": 24,
    "peak_fraction": 0.5,
    "recovery_steps": 3,
}
SPLIT = {"calibration": [1, 2], "validation": [3], "test": [4, 5, 6]}


def make_wide(n_stations: int = 3, n_weeks: int = 6, seed: int = 0) -> pd.DataFrame:
    """Wide speed frame (index ts, one column per station) with no missing values."""
    rng = np.random.default_rng(seed)
    idx = period(START, n_weeks)
    hour = idx.hour + idx.minute / 60
    weekday = idx.dayofweek < 5
    rush = 18 * np.exp(-((hour - 8) ** 2) / 2) + 22 * np.exp(-((hour - 17.5) ** 2) / 2)
    base = 65 - np.where(weekday, rush, 0.3 * rush)
    cols = {f"S{k}": base + rng.normal(0, 2, len(idx)) for k in range(n_stations)}
    return pd.DataFrame(cols, index=idx).clip(lower=5)


def make_long(n_stations: int = 3, n_weeks: int = 6, seed: int = 0) -> pd.DataFrame:
    wide = make_wide(n_stations, n_weeks, seed)
    long = wide.stack().rename("speed").reset_index()
    long.columns = ["ts", "station", "speed"]
    long["imputed"] = False
    return long[["station", "ts", "speed", "imputed"]]
