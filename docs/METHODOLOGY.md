# Synthetic experiment methodology

## Generator and provenance
Seed 2026 creates 160 fictional type-2-diabetes profiles and 322,560 sensor rows over seven days. No real data were fitted or copied. The clock begins 2026-01-01 and is timezone-naive for deterministic demonstration. Profile baseline is drawn uniformly from 100–157 mg/dL. Age is 30–78, diabetes duration 1–21 years. HbA1c is an illustrative baseline-associated value with random noise, not a physiological conversion or diagnostic calculation. Sex and medication fields are descriptive; the model does not use them. No medication response is simulated.

The glucose generator is baseline + delayed meal responses - activity response + circadian oscillation + prior-night sleep term + autocorrelated noise + sensor noise, clipped to 60–350 mg/dL. Each day has three jittered meal events, with a hidden meal load and hidden patient response multiplier. A meal kernel uses x*exp(1-x), x = elapsed samples/10. This creates a delayed peak near 50 minutes. Kernel amplitude and patient sensitivity never enter model features. Two short activity periods drive steps and heart rate, with a decaying glucose association. These coefficients are programmed assumptions, not validated physiological parameters. Circadian and habitual meal schedules make some events predictable; this is a simulator-specific advantage.

Noise follows AR(1) with coefficient 0.92 plus measurement noise. About 1.2% of glucose values are independently missing, with a further six-sample contiguous gap per patient. Heart rate and HRV have activity-associated changes and noise. Sleep duration at each time represents a previously completed sleep record; the model never receives upcoming sleep. HRV and activity_event are generated but excluded from the estimator; activity is represented by steps and heart rate.

## Causal feature construction
Training and replay call the same features() function. All rolling windows are trailing and include the current observation. At most three missing glucose samples are forward-filled. No backfill, centered rolling windows or future statistics. Raw missingness is preserved as a feature. Beyond 15 minutes without CGM or >25% missing in the last 12 observations, inference is withheld. A missing latest observation can still permit an estimate based on a recent reading; the dashboard says Missing for the latest actual measurement. Native histogram boosting handles residual NaNs.

Personalization uses historical baseline glucose, HbA1c, diabetes duration, historical fasting glucose, current-minus-historical-baseline and current-minus-expanding-past-mean. There is no per-patient fitting using held-out future data. Baselines are synthetic historical variables generated before the stream, not full-timeline averages. The population comparator removes all historical and explicitly personalized features. It does not isolate each normalization variable separately.

## Target and splitting
Label=1 if any of the next 24 five-minute glucose observations is strictly >180 mg/dL. Current t excluded, t+120 included. Missing/truncated future horizons excluded. Warmup=12 observations; anchors every 3 observations. Eligibility rules match inference. Patients are shuffled once with seed 2026 into 55/15/15/15 percent training/validation/calibration/test partitions. Overlapping windows from one patient never cross partitions. Overlap within a partition remains, so effective sample size is much smaller than window count.

## Estimator selection
Scikit-learn HistGradientBoostingClassifier with 100 boosting iterations, learning rate 0.08, L2=5, random seed 2026, and early_stopping=False. Compare 7 versus 15 leaves using validation average precision; no random row-level internal validation split. Fit sigmoid/logistic calibration on separate calibration patients using the model probability logit. Fixed alert cutoff=0.5; no test tuning. There is no XGBoost model and no regression forecast.

Class prevalence is about 36% in test. We retain natural synthetic prevalence without oversampling or class weights, use PR metrics, report prevalence, and measure both false positives and false negatives. No balancing claim is made. Future unseen clinical datasets may have very different prevalence.

## Baseline, explanations and scenarios
Rule: latest forward-filled glucose + 120*max(15-minute slope,0) >180. It outputs a binary decision. Its AP and Brier values are calculated on binary scores and are not probability calibration estimates. Local sensitivity replaces one feature at a time with its training median and computes original probability minus modified probability. This is not additive, not SHAP, and not causal. Correlated features can yield inconsistent replacements. Global importance is permutation decrease in validation AP (two repeats, up to 2,500 rows), with correlated-feature limitations.

Scenario controls edit a copy of the observed prefix and recalculate ALL features. Activity edits steps and heart rate; meal edits the annotation only, not a causal future response. Profile swaps deliberately stress the EHR inputs while holding the observed stream constant. These combinations can be out of distribution and must not be interpreted as intervention effects.

## Evaluation and limits
All reported metrics are computed from the held-out 24 patients. The primary fused model beats the simple rule but does not beat the dynamic-only ablation. Calibration slightly worsens test Brier. Early-warning subset excludes currently elevated glucose and has lower performance than the main result. All are disclosed.

No real CGM validation, prospective testing, external population evaluation, subgroup fairness study, episode-level alert burden, confidence interval, uncertainty interval, or patient-level bootstrap has been implemented. No alarm suppression/cooldown, authentication, clinical interoperability or wearable ingestion. This is a local research demonstrator.

## References
- scikit-learn probability calibration guide: https://scikit-learn.org/stable/modules/calibration.html
- HistGradientBoostingClassifier API: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html
- Streamlit testing API: https://docs.streamlit.io/develop/api-reference/app-testing
These support software methodology, not the clinical validity of this simulator. The 180 mg/dL threshold is a configurable experiment definition supplied in the participant brief, not a diagnostic rule.
