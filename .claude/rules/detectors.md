---
paths:
  - "src/sa_adwin/detectors/**"
---
- ADWIN: clock=1, inputs scaled to [0,1] with Scaler01 fitted on calibration weeks only.
- Use our own Holt-Winters (River 0.26.1 additive bug, issue #2077). O(1) per update.
- HW robust update: if |residual| > k*sd, learn from the clipped value.
- Emit two-sided Signals (direction -1/+1); never filter direction inside a detector.
