"""Run S1-S3 once: QC, choose stations, split, inject. Writes only to data/processed/.

python scripts/prepare_data.py --config configs/base.yaml
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from sa_adwin.data import ingest
from sa_adwin.data.inject import inject
from sa_adwin.data.split import split


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/base.yaml")
    cfg = yaml.safe_load(Path(ap.parse_args().config).read_text())
    d, start = cfg["data"], cfg["data"]["start"]

    if d["source"] == "pems_bay":
        wide = ingest.load_pems_bay(d["pems_bay_h5"], start, d["n_weeks"])
    else:
        wide = ingest.load_pems_dir(d["pems_dir"], start, d["n_weeks"])
    if d["stations"]:
        wide = wide[[str(s) for s in d["stations"]]]

    long, qc = ingest.quality_check(wide, d["min_observed"], d["max_fill_steps"])
    stations = ingest.choose_stations(qc, d["n_stations"])
    long = long[long["station"].isin(stations)]

    out = Path(d["processed_dir"])
    out.mkdir(parents=True, exist_ok=True)
    qc.to_csv(out / "qc.csv", index=False)
    ingest.save_processed(long, out)

    parts = split(long, start, cfg["split"])
    for name, seeds in [("validation", cfg["inject"]["seeds_validation"]),
                        ("test", cfg["inject"]["seeds_test"])]:  # fmt: skip
        for seed in seeds:
            series, labels = inject(parts[name], cfg["inject"], seed, start)
            series.to_parquet(out / f"{name}_seed{seed}.parquet", index=False)
            labels.to_csv(out / f"labels_{name}_seed{seed}.csv", index=False)
    parts["calibration"].to_parquet(out / "calibration.parquet", index=False)

    print(f"QC: {int(qc['kept'].sum())}/{len(qc)} stations kept, using {len(stations)}")
    print({k: len(v) for k, v in parts.items()}, "rows per split ->", out)


if __name__ == "__main__":
    main()
