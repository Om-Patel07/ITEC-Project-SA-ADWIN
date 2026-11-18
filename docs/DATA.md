# Data: what to download and where to put it

Nothing under `data/` is committed. Each teammate downloads the files by hand.

## Now (Week 1): PEMS-BAY, the fallback
- Get `pems-bay.h5` from the DCRNN repo README (https://github.com/liyaguang/DCRNN),
  "Data Preparation" section (Google Drive / Baidu link). Only this one file is needed.
- Save it as `data/raw/pems-bay.h5`.
- Contents: 325 Bay Area sensors, average speed (mph), 5-min, Jan 1 - May 31 2017.
  Zeros mean "missing"; the loader turns them into NaN.
- Window in `configs/base.yaml`: Mon 2017-02-27 to Sun 2017-04-09 (6 weeks, no US holiday).

## Later: PeMS Clearinghouse (the real target)
1. Register at https://pems.dot.ca.gov (approval takes 1-2 business days).
2. Data Clearinghouse -> Type: **Station 5-Minute**, District: **4 (Bay Area)**.
   Download one file per day by hand (no scripted downloads; Caltrans disallows them).
   Pick 6 consecutive Monday-to-Sunday weeks with no public holiday.
3. Same page, Type: **Station Metadata**, one file for that period.
4. Put the daily `d04_text_station_5min_YYYY_MM_DD.txt.gz` files in `data/raw/pems/`.
5. In `configs/base.yaml` set `source: pems`, `start:` to the first Monday.

Then run `python scripts/prepare_data.py --config configs/base.yaml`.
It writes `data/processed/`: `qc.csv`, `stations/*.parquet`, `calibration.parquet`,
`{validation,test}_seed*.parquet` and `labels_*_seed*.csv`.

## Data use and protection (everyone must follow)
- **Own account each.** Every teammate registers their own PeMS account. Never share a
  login, and never put usernames, passwords or tokens in the repo (`.env` is not committed).
- **No raw or processed data in git.** `/data/` and `/runs/` are git-ignored; the repo is
  public, so share data only privately within the team (e.g. a shared drive), not on GitHub.
- **Download by hand, at low volume.** The PeMS Conditions of Use forbid using the system
  "for other than its intended purposes" and attempts to defeat its security. We do not
  script logins or bulk scraping.
- **Attribution.** The report and README cite "Caltrans Performance Measurement System
  (PeMS), https://pems.dot.ca.gov" and, for PEMS-BAY, Li et al. 2018 (DCRNN, ICLR).
- **No personal data.** PeMS loop-detector data is aggregated speed/flow per station; it
  holds no personal information. Do not join it with any data that does.
- **Results we publish** (tables, plots, metrics) are derived aggregates and fine to share.
