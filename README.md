# GlucoTwin
## A Personalized, Continuously Updating Digital Twin for Early Prediction of Glucose Excursions
**From Reactive Glucose Monitoring to Personalized Predictive Health.**

Research proof-of-concept for the participant-described Happiest Health Digital Twin Challenge 2026. **All patients and sensors are synthetic. No clinical validation, diagnosis, treatment recommendations, or demonstrated clinical benefit.** Competition requirements and dates come from the participant brief, not independently verified rules.

### Run locally (Python 3.11 or 3.12)
```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
The supplied package contains generated data and the trained model. Open http://localhost:8501. No keys, cloud services, or accounts are needed. Only load the trusted bundled joblib model: pickle-based formats can execute code.

### Reproduce the experiment
```bash
# Stop Streamlit before retraining. Restart it afterwards to clear cached resources.
python -m glucotwin.train --patients 160 --days 7 --seed 2026 --threshold 180 --horizon 120
python -m pytest -q
python scripts/build_submission.py
```
On systems with too many BLAS/OpenMP workers, set `OMP_NUM_THREADS=2` and `OPENBLAS_NUM_THREADS=2`. First dependency installation needs internet. App execution is local afterwards. Python 3.12.14 was used for the executed run. Direct dependency versions are pinned; `environment-lock.txt` records the tested environment. Exact float results can vary slightly across platforms.

### What works
- 160 persistent synthetic patient profiles, each with seven days of 5-minute sensor observations.
- Fusion of historical EHR-like characteristics and strictly past/current sensor features.
- A trained scikit-learn histogram gradient boosting event classifier, rule baseline, and dynamic-only ablation.
- Four disjoint patient partitions: 88 training, 24 validation, 24 calibration, 24 test.
- Deterministic Start/Resume, Pause, Reset, 5-minute Step and 1-hour Advance controls.
- Per-patient session state, changing predictions and persistent SQLite audit records.
- Seven dashboard pages, missing-data withholding, model sensitivity, scenario edits and exports.
- Genuine held-out metrics, reliability diagram, PR curve, and confusion matrix.

### Prediction contract
At time t, predict whether **any available simulated CGM value exceeds 180 mg/dL at t+5,...,t+120 minutes**. No duration criterion. The current reading is excluded from the label. An already-elevated current reading is allowed; therefore the main task includes persistence of existing excursions as well as new excursions. A separate below-threshold-at-t subset is reported to avoid overstating early warning.

Only anchors with a complete future horizon are labeled. This conservatively excludes missing future values even when an observed positive might already establish an event. Training/evaluation uses 15-minute anchors after a 60-minute warmup. Live inference can run every 5 minutes; evaluation metrics apply to the 15-minute sampling protocol. Threshold and horizon belong to the trained bundle. Change them through retraining, not a cosmetic dashboard slider.

### Executed results: synthetic held-out patients
| Model | Precision | Recall | F1 | Average precision (PR-AUC) | Brier |
|---|---:|---:|---:|---:|---:|
| Fused EHR + sensor model | 0.8727 | 0.8188 | 0.8449 | 0.9498 | 0.0695 |
| Glucose + positive trend rule | 0.7232 | 0.5540 | 0.6274 | 0.5621 | 0.2383 |
| Dynamic-only ablation | 0.8831 | 0.8138 | 0.8470 | 0.9508 | 0.0693 |

11,567 test windows; prevalence 36.21%. Fused confusion matrix: TN 6,879, FP 500, FN 759, TP 3,429. False-positive rate 6.78%; 4.32 false-positive **windows** per 100 evaluated windows. These are correlated windows, not distinct alert episodes. No confidence intervals or significance claims are made.

Below-threshold subset: 9,696 windows, F1 0.7447, recall 0.7000, average precision 0.8678. The dynamic-only model slightly outperformed fusion on this seed: **no demonstrated personalization improvement**. Raw Brier was 0.06867 versus 0.06952 after calibration: calibration did not improve this test score. Brier measures more than calibration alone. Read `artifacts/metrics.json` for the source of every result and exact partition IDs.

### Why this is a digital twin
A persistent synthetic identity joins baseline history to a timestamped stream. The twin maintains its current position, causal rolling features, latest observation, data-quality state, prediction and prediction history. Each arrival rebuilds features from the available prefix and calls the trained model. Switching patients restores separate session states. SQLite persists issued estimates across app restarts; replay cursor state itself is session-local. Reset clears replay state, not the audit database. Future observations only appear in an explicitly labeled retrospective view.

This is a **data-driven monitoring twin**, not a mechanistic physiological twin or a validated intervention simulator. It uses a shared population model conditioned on patient history and personal deviations; it does not fit an individual patient's future data.

### Architecture and files
```text
app.py                     Streamlit application
  glucotwin/data.py        Seeded EHR and sensor generator
  glucotwin/features.py    Shared causal feature and target construction
  glucotwin/train.py       Partition, train, calibrate, evaluate, export
  glucotwin/twin.py        Replay state, model calls, SQLite audit
  data/patients.csv        Historical synthetic profiles
  data/sensors/*.csv.gz    Separate patient timelines
  artifacts/model.joblib  Trained estimator + calibration + configuration
  artifacts/metrics.json  Evaluation and partition manifest
  artifacts/test_predictions.csv  Recomputable test outcomes
  docs/                   Methodology, data dictionary, demo script, PDFs
  tests/                  Temporal isolation, state, labels, UI integration
```

The separately delivered `GLUCOTWIN_DEMO.mp4` is a 23m 53s edited screen walkthrough using actual app captures and synthesized narration. Its script and chapter list are in this package. It is not an uninterrupted live recording.

See `docs/ARCHITECTURE.pdf`, `docs/GLUCOTWIN_PRESENTATION.pdf`, `docs/METHODOLOGY.md`, `docs/DATA_DICTIONARY.md`, `docs/MODEL_CARD.md`, and `docs/DEMO_SCRIPT.md`.

### Dashboard tour
1. **Executive Overview:** latest synthetic observation, estimate, time and quality.
2. **Patient Profile:** EHR-like record with historical provenance.
3. **Live Digital Twin:** Start/Resume, Pause, Step, Advance, Reset and state inspector. A shaded future area means the classification horizon, not a glucose forecast.
4. **Risk and Explainability:** median-replacement local sensitivity, not SHAP or causation.
5. **Scenario Simulator:** edit only a copied input prefix; compare estimates or see withholding.
6. **Model Performance:** test metrics, dynamic-only comparison, PR and calibration curves.
7. **Prediction Log:** persistent audit, CSV export and opt-in retrospective ground truth.

### Team and submission
Project/Team Name: GlucoTwin (Registered as Team MeowMeow). Participants: J K Raj Vamshi Thakur from the Indian Institute of Information Technology, Allahabad (B.Tech ECE, 2023–2027), and Swasti Mishra from IIT Dhanbad (ECE). No additional teammates, mentors, or incubator affiliations are claimed. Participants must verify eligibility and affiliation wording before submission.
The repository is GitHub-compatible. This package does not claim a public repository or video link has been published. Follow `docs/SUBMISSION_CHECKLIST.md` for the remaining external publication steps. Keep the generated artifacts alongside code so judges can run the demo immediately.

### License and integrity
Project code, documentation and newly generated synthetic data: MIT (`LICENSE`). Third-party dependencies retain their own licenses (`THIRD_PARTY.md`). No patient records, real identities, proprietary datasets or trained clinical models were used. Synthetic generation rules are assumptions and cannot support real-world efficacy claims. No medication changes or clinical actions are recommended.

### Optional demonstration asset regeneration
`python scripts/build_submission.py` regenerates the PDFs. Browser captures use `scripts/capture_demo.py` and optional Playwright 1.55.0 plus its Chromium install. The edited narrated MP4 is delivered separately to keep the source archive small. To rebuild it on Linux, use `scripts/build_video.py` with Pillow, DejaVu Sans fonts, ffmpeg with the `flite` filter, and ffprobe. These optional production tools are not needed to run the app. The demo captures were inspected at 1440×1000; the produced video has a 1600×1200 frame and audible synthetic narration. Review whether edited captures and synthetic narration satisfy the competition's current video policy before submission.
