"""S2: fixed calibration / validation / test weeks (never changed after Week 1)."""

from __future__ import annotations

import pandas as pd


def week_number(ts: pd.Series, start: str) -> pd.Series:
    """1-based week number counted from `start` (a Monday at midnight)."""
    return ((ts - pd.Timestamp(start)) // pd.Timedelta(weeks=1)).astype(int) + 1


def split(long: pd.DataFrame, start: str, weeks: dict[str, list[int]]) -> dict[str, pd.DataFrame]:
    """Return {"calibration": df, "validation": df, "test": df} by week number."""
    wk = week_number(long["ts"], start)
    return {name: long[wk.isin(nums)].reset_index(drop=True) for name, nums in weeks.items()}
