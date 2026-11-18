---
paths:
  - "src/sa_adwin/eval/**"
---
- Event-based scoring only, no point-adjust.
- Detected = alert starts in [onset, end + 15 min). Unmatched alert = false alert.
- Report false alerts per station-day (overall and peak), recall, precision, median/p90 latency.
