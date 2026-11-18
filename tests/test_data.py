import gzip

import numpy as np
import pandas as pd
import pytest
from fixtures import INJECT_CFG, SPLIT, START, make_long, make_wide

from sa_adwin.contracts import Signal
from sa_adwin.data import ingest
from sa_adwin.data.inject import inject, is_peak, profile
from sa_adwin.data.split import split, week_number
from sa_adwin.data.stream import replay, run_stream


# --- S1 QC ---------------------------------------------------------------
def test_qc_fills_short_gaps_only_and_flags_them():
    wide = make_wide(n_stations=2, n_weeks=1)
    wide.iloc[100:103, 0] = np.nan  # 3-step gap -> filled
    wide.iloc[200:204, 0] = np.nan  # 4-step gap -> stays missing
    long, qc = ingest.quality_check(wide, min_observed=0.9, max_fill_steps=3)
    s0 = long[long["station"] == "S0"].reset_index(drop=True)
    assert s0.loc[100:102, "imputed"].all() and s0.loc[100:102, "speed"].notna().all()
    assert s0.loc[200:203, "speed"].isna().all() and not s0.loc[200:203, "imputed"].any()
    assert qc.set_index("station").loc["S0", "long_gap_steps"] == 4


def test_qc_drops_station_under_threshold():
    wide = make_wide(n_stations=2, n_weeks=1)
    wide.iloc[::5, 1] = np.nan  # 80% observed
    long, qc = ingest.quality_check(wide, min_observed=0.9)
    assert set(long["station"]) == {"S0"}
    assert ingest.choose_stations(qc, 5) == ["S0"]


def test_load_pems_dir_parses_clearinghouse_format(tmp_path):
    lines = [
        "02/27/2017 00:00:00,400001,4,101,N,ML,0.5,10,100,50,0.05,64.5",
        "02/27/2017 00:05:00,400001,4,101,N,ML,0.5,10,0,50,0.05,61.0",  # imputed by PeMS
        "02/27/2017 00:00:00,400002,4,101,N,OR,0.5,10,100,50,0.05,30.0",  # on-ramp, dropped
    ]
    path = tmp_path / "d04_text_station_5min_2017_02_27.txt.gz"
    with gzip.open(path, "wt") as f:
        f.write("\n".join(lines) + "\n")
    wide = ingest.load_pems_dir(tmp_path, START, n_weeks=1)
    assert list(wide.columns) == ["400001"]
    assert wide.iloc[0, 0] == 64.5 and np.isnan(wide.iloc[1, 0])
    assert len(wide) == 2016


# --- S2 split ------------------------------------------------------------
def test_split_weeks_are_disjoint_and_complete():
    long = make_long(n_stations=1)
    parts = split(long, START, SPLIT)
    assert sum(len(p) for p in parts.values()) == len(long)
    assert set(week_number(parts["validation"]["ts"], START)) == {3}
    assert parts["test"]["ts"].min() > parts["validation"]["ts"].max()


# --- S3 inject -----------------------------------------------------------
def test_profile_shapes():
    f = profile(3, 0.5, "sudden", recovery_steps=3)
    assert np.allclose(f, [0.5, 0.5, 0.5, 0.625, 0.75, 0.875])
    g = profile(6, 0.35, "gradual", recovery_steps=0)
    assert g[0] > g[1] > g[2] and np.allclose(g[2:], 0.65)


def test_inject_labels_follow_rules():
    test = split(make_long(n_stations=3), START, SPLIT)["test"]
    series, labels = inject(test, INJECT_CFG, seed=1, start=START)
    assert len(labels) == 3 * 3 * 2  # stations x weeks x per_station_week
    assert set(labels["severity"]) <= {0.2, 0.35, 0.5}
    assert labels["peak"].mean() == 0.5
    assert is_peak(pd.DatetimeIndex(labels.loc[labels["peak"], "onset"])).all()
    for _, g in labels.groupby("station"):
        assert (g["onset"].diff().dropna() >= pd.Timedelta(hours=24)).all()


def test_inject_changes_only_incident_windows_and_is_seeded():
    test = split(make_long(n_stations=2), START, SPLIT)["test"].sort_values(["station", "ts"])
    a, la = inject(test, INJECT_CFG, seed=7, start=START)
    b, lb = inject(test, INJECT_CFG, seed=7, start=START)
    pd.testing.assert_frame_equal(la, lb)
    changed = ~np.isclose(a["speed"].to_numpy(), test["speed"].to_numpy())
    assert (changed <= a["injected"].to_numpy()).all()
    assert (
        a.loc[a["injected"], "speed"].to_numpy() < test["speed"].to_numpy()[a["injected"]]
    ).all()


# --- S4 replay -----------------------------------------------------------
def test_replay_is_time_ordered_and_skips_missing():
    long = make_long(n_stations=2, n_weeks=1)
    long.loc[5, "speed"] = np.nan
    recs = list(replay(long))
    assert len(recs) == len(long) - 1
    assert all(a.ts <= b.ts for a, b in zip(recs[:-1], recs[1:], strict=True))


def test_detector_never_sees_future_values():
    long = make_long(n_stations=2, n_weeks=1)
    latest = {"ts": None}

    class Spy:
        name = "spy"

        def __init__(self, station):
            self.station, self.seen = station, []

        def update(self, rec):
            assert rec.station == self.station
            assert latest["ts"] is None or rec.ts >= latest["ts"]
            latest["ts"] = rec.ts
            self.seen.append(rec.ts)
            return Signal(rec.station, rec.ts, self.name, -1) if rec.speed < 40 else None

    sigs = run_stream(replay(long), Spy, "spy")
    assert sigs and all(s.direction == -1 for s in sigs)


def test_run_stream_rejects_backdated_signal():
    class Cheater:
        name = "cheat"

        def __init__(self, station):
            pass

        def update(self, rec):
            return Signal(rec.station, rec.ts - pd.Timedelta(minutes=5), self.name, -1)

    with pytest.raises(ValueError):
        run_stream(replay(make_long(n_stations=1, n_weeks=1)), Cheater, "cheat")
