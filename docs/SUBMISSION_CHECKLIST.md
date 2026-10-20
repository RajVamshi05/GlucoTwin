# Submission handoff
Prepared from the participant brief. Verify official instructions before submitting.

## Included
- Runnable Streamlit project and pinned direct dependencies.
- Synthetic data, trained model, reproducible generator and evaluation.
- README, MIT license, methodology, data dictionary and model card.
- Architecture PDF and project presentation PDF.
- Test suite and test output.
- 23m 53s narrated edited screen walkthrough (MP4, delivered separately), with source narration and chapter timings.

## External actions still required unless a confirmed URL accompanies delivery
1. Create a public GitHub repository, e.g. `glucotwin`, and push this folder.
2. Review the supplied 23m 53s walkthrough. It uses edited app captures and synthetic speech. If the competition requires a continuous or participant-narrated recording, record your own version using docs/DEMO_SCRIPT.md.
3. Upload the recording to an allowed host, set access for judges and test in an incognito window.
4. Insert the actual repository and video links into the submission form. Never submit guessed or placeholder URLs.
5. Verify team membership, college, event rules, deadline and any required consent/declarations.

Suggested commands after creating an EMPTY public repository in your account:
```bash
git init
git add .
git commit -m "Build GlucoTwin synthetic digital twin proof of concept"
git branch -M main
git remote add origin https://github.com/YOUR_ACCOUNT/glucotwin.git
git push -u origin main
```
No public repository or hosted video is claimed by these instructions. Do not publish local virtual environments, SQLite session logs or secrets. The default .gitignore excludes them.

## Demo acceptance checks
- Start/Resume changes timestamp and prediction; Pause stops progression.
- Step changes the state by five simulated minutes; Reset restores initial cursor.
- Switch patients and verify their EHR and timeline change.
- Missing-interval scenario withholds the estimate.
- Only retrospective mode reveals the complete future ground truth.
- Read test metrics from artifacts/metrics.json rather than manually entering scores.
