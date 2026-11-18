"""S0-S1: load raw speed data, quality-check it and fill short gaps.

Data is kept "wide" while loading (index = 5-min timestamp, one column per
station) and "long" afterwards (columns: station, ts, speed, imputed).
Raw files in data/raw are only ever read, never written.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

FREQ = "5min"

# Clearinghouse "Station 5-Minute" files have no header; the first 12 columns are fixed.
PEMS_COLUMNS = [
    "ts", "station", "district", "freeway", "direction", "lane_type",
    "station_length", "samples", "pct_observed", "flow", "occupancy", "speed",
]  # fmt: skip


def period(start: str, n_weeks: int) -> pd.DatetimeIndex:
    """The full 5-min grid for n_weeks starting at midnight on `start`."""
    t0 = pd.Timestamp(start)
    return pd.date_range(t0, t0 + pd.Timedelta(weeks=n_weeks), freq=FREQ, inclusive="left")


def load_pems_bay(h5_path: str | Path, start: str, n_weeks: int) -> pd.DataFrame:
    """PEMS-BAY (DCRNN repo): 325 sensors, mph. Zeros mean missing, so they become NaN."""
    df = pd.read_hdf(h5_path)
    df.columns = df.columns.astype(str)
    df = df.reindex(period(start, n_weeks))
    return df.mask(df <= 0)


def load_pems_dir(pems_dir: str | Path, start: str, n_weeks: int) -> pd.DataFrame:
    """Clearinghouse daily files (dNN_text_station_5min_YYYY_MM_DD.txt.gz), mainline only.

    Rows where PeMS observed nothing (pct_observed == 0) are PeMS-imputed and become NaN.
    """
    idx = period(start, n_weeks)
    frames = []
    for day in pd.date_range(idx[0], idx[-1], freq="D"):
        hits = sorted(Path(pems_dir).glob(f"*_text_station_5min_{day:%Y_%m_%d}.txt*"))
        if not hits:
            continue
        raw = pd.read_csv(hits[0], header=None, usecols=range(12), names=PEMS_COLUMNS)
        raw = raw[raw["lane_type"] == "ML"]
        frames.append(raw[["ts", "station", "pct_observed", "speed"]])
    if not frames:
        raise FileNotFoundError(f"no station 5-min files for {start} (+{n_weeks} wk) in {pems_dir}")
    df = pd.concat(frames, ignore_index=True)
    df["ts"] = pd.to_datetime(df["ts"], format="%m/%d/%Y %H:%M:%S")
    df.loc[df["pct_observed"] <= 0, "speed"] = np.nan
    wide = df.pivot_table(index="ts", columns="station", values="speed", aggfunc="first")
    wide.columns = wide.columns.astype(str)
    return wide.reindex(idx)


def _gap_lengths(missing: pd.Series) -> pd.Series:
    """For each missing step, the length of the run of missing steps it belongs to."""
    run_id = (missing != missing.shift()).cumsum()
    return missing.groupby(run_id).transform("size").where(missing, 0)


def quality_check(
    wide: pd.DataFrame, min_observed: float = 0.90, max_fill_steps: int = 3
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Drop stations under `min_observed`; fill gaps of <= max_fill_steps by linear interpolation.

    Returns (long frame, QC table). Longer gaps stay NaN; the stream replay skips them.
    """
    rows, parts = [], []
    for station in wide.columns:
        s = wide[station]
        observed = float(s.notna().mean())
        gaps = _gap_lengths(s.isna())
        fill = s.isna() & (gaps <= max_fill_steps)
        filled = s.interpolate(limit_area="inside").where(fill, s)
        keep = observed >= min_observed
        rows.append({
            "station": station, "observed": observed, "filled_steps": int(fill.sum()),
            "long_gap_steps": int(filled.isna().sum()), "kept": keep,
        })  # fmt: skip
        if keep:
            parts.append(pd.DataFrame({
                "station": station, "ts": wide.index,
                "speed": filled.to_numpy(), "imputed": fill.to_numpy(),
            }))  # fmt: skip
    qc = pd.DataFrame(rows)
    long = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["station", "ts", "speed", "imputed"])
    return long, qc


def choose_stations(qc: pd.DataFrame, n: int) -> list[str]:
    """The n kept stations with the most observed data (ties broken by station id)."""
    kept = qc[qc["kept"]].sort_values(["observed", "station"], ascending=[False, True])
    return kept["station"].head(n).tolist()


def save_processed(long: pd.DataFrame, out_dir: str | Path) -> None:
    """One parquet file per station in data/processed/stations/."""
    out = Path(out_dir) / "stations"
    out.mkdir(parents=True, exist_ok=True)
    for station, part in long.groupby("station"):
        part.to_parquet(out / f"{station}.parquet", index=False)
