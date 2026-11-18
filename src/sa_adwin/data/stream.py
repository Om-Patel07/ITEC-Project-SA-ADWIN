"""S4: replay data as a stream, one record at a time in time order.

Detectors only ever receive the current record, so they cannot read the future.
Steps whose speed is still missing after QC (long gaps) are skipped.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

import pandas as pd

from sa_adwin.contracts import Detector, Record, Signal


def replay(long: pd.DataFrame) -> Iterator[Record]:
    """Yield Records ordered by (timestamp, station), skipping missing speeds."""
    df = long.dropna(subset=["speed"]).sort_values(["ts", "station"], kind="stable")
    imputed = df["imputed"] if "imputed" in df else pd.Series(False, index=df.index)
    for station, ts, speed, imp in zip(df["station"], df["ts"], df["speed"], imputed):
        yield Record(station=str(station), ts=pd.Timestamp(ts), speed=float(speed), imputed=bool(imp))


def run_stream(stream: Iterable[Record], make_detector, method: str) -> list[Signal]:
    """Feed the stream to one detector per station; collect the raw Signals.

    `make_detector(station)` returns a fresh Detector. A Signal must carry the
    timestamp of the record that produced it (no look-ahead, no back-dating).
    """
    detectors: dict[str, Detector] = {}
    signals: list[Signal] = []
    for rec in stream:
        det = detectors.get(rec.station)
        if det is None:
            det = detectors[rec.station] = make_detector(rec.station)
        sig = det.update(rec)
        if sig is not None:
            if sig.ts != rec.ts:
                raise ValueError(f"{method}: signal ts {sig.ts} != record ts {rec.ts}")
            signals.append(sig)
    return signals
