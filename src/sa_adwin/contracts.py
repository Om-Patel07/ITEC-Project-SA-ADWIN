"""Shared types used by data, detectors and eval.

Changing anything in this file needs approval from all 3 team members.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import pandas as pd

STEP_MINUTES = 5
STEPS_PER_DAY = 288
STEPS_PER_WEEK = 2016


@dataclass(frozen=True)
class Record:
    """One 5-minute reading for one station, as yielded by the stream replay."""

    station: str
    ts: pd.Timestamp
    speed: float
    imputed: bool = False


@dataclass(frozen=True)
class Signal:
    """A raw change signal from a detector, before post-processing.

    direction: -1 = speed dropped, +1 = speed rose. Detectors emit both;
    only eval/postprocess.py filters by direction.
    """

    station: str
    ts: pd.Timestamp
    method: str
    direction: int
    score: float = 0.0


@dataclass(frozen=True)
class Incident:
    """One injected incident (a row of labels.csv)."""

    station: str
    onset: pd.Timestamp
    end: pd.Timestamp
    severity: float
    onset_type: str  # "sudden" or "gradual"
    peak: bool


LABEL_COLUMNS = ["station", "onset", "end", "severity", "onset_type", "peak"]


class Detector(Protocol):
    """Every method implements this. It sees one record at a time, never the future."""

    name: str

    def update(self, record: Record) -> Signal | None: ...
