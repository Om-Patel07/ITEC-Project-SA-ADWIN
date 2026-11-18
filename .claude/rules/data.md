---
paths:
  - "src/sa_adwin/data/**"
---
- Never modify files in data/raw. Write processed parquet to data/processed/.
- Keep mainline stations with >= 90% observed; fill gaps <= 3 steps and mark imputed=True.
- Injection: severity 20/35/50%, duration 15/30/60 min, half in weekday peaks, >= 24 h apart.
- Inspect data with pandas summaries (nrows=, describe()), never by printing whole files.
