# Verification report

Executed in Python 3.12.14 using the versions recorded in requirements.txt.

- Eight pytest tests passed, including a multi-page Streamlit AppTest.
- Synthetic generation reproduced identical records for the same seed.
- Modifying future sensor rows left earlier features unchanged.
- Live prefix features matched the corresponding full-frame past features.
- Label tests excluded current glucose, included the final horizon observation and removed missing/incomplete horizons.
- Patient partitions were pairwise disjoint.
- Stale glucose correctly withheld inference.
- Twin advancement, reset, end-of-stream clamping and idempotent SQLite logging passed.
- AppTest visited every page, exercised scenarios and switched patients.
- Chromium opened the actual app and exercised Start, Pause, Step, Advance, all scenarios, performance and retrospective inspection with no rendered application exception.
- PDFs rendered to page images and were inspected for layout and text clipping.
- Recalculated F1, average precision and confusion matrix match the saved per-window test predictions.

Scope: local single-user demonstration. No independent machine install, real-device integration, concurrent-user test, clinical validation or public-link access test was performed. The narrated demonstration uses edited real application captures and a synthetic voice, not continuous real-time recording.
