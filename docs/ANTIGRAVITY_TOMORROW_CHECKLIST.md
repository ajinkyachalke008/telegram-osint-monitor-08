# Tomorrow's Demo — Operator Checklist

## Before the judges arrive
- [ ] Clone/pull the repository and checkout `feat/ps02-hackathon-dataset-demo` (or the PR branch supplied by the project owner).
- [ ] Use the documented Python version and create/activate a virtual environment.
- [ ] Install dependencies from `requirements.txt`.
- [ ] Keep the supplied `PS02_demo_data-20261127T071007Z-1-001.zip` local; do not commit it.
- [ ] Start the application using the new nondestructive command documented by Antigravity.
- [ ] Select the participant ZIP in the dataset page.
- [ ] Run preflight and inspect errors/warnings.
- [ ] Run dry-run; verify counts are plausible and errors are zero or understood.
- [ ] Import once, confirm success summary.
- [ ] Import again; confirm deduplication/idempotence (no doubled counts).
- [ ] Open aggregate dashboard and confirm every chart says participant dataset / correct batch.
- [ ] Confirm existing pages still open and synthetic demo pages remain labeled synthetic.
- [ ] Confirm no raw participant messages, author names, handles, phone/payment values or precise identifying detail appears in charts, logs or screenshots.
- [ ] Capture one screenshot of dataset preflight, one of aggregate analytics, one of provenance/report.
- [ ] Rehearse the 3–4 minute flow below.

## Demo narrative (3–4 minutes)
1. **Problem and dataset:** “The hackathon provided a multi-platform dataset. We built a reproducible intake and validation flow around the provided material.”
2. **Preflight:** Select the ZIP. Show the measured runtime inventory, source counts, schema/time checks and poster hash result.
3. **Analytics:** Show actual aggregate distribution by platform/time, attachment references and data-quality results.
4. **Existing application:** Demonstrate one previously built feature using its own clearly labeled synthetic fixture, without implying it was derived from the participant data.
5. **Integrity and limitations:** Show batch provenance and explain that hashes verify integrity against the provided manifest, not factual truth; automated signals are not proof.
6. **Close:** “We can reproduce the same aggregate dataset report from the same input file, and re-import is safe and idempotent.”

## Never do this in the demo
- Do not claim participant data proves a named person or account is involved in wrongdoing.
- Do not expose raw authors, usernames, contact/payment identifiers, or raw text.
- Do not describe synthetic benchmark accuracy as accuracy on the hackathon dataset.
- Do not claim the dataset contains a judge answer key or ground-truth labels.
- Do not click destructive reset buttons on the existing database.
- Do not claim a live feed is live when it is replay/synthetic.
- Do not leave the dataset ZIP, extracted source files or populated DB staged for Git commit.
