# Tomorrow's PS02 Demo — Operator Checklist

## Laptop preparation
- [ ] Pull repository and checkout `feat/ps02-hackathon-handoff-v2` (or the latest handoff branch).
- [ ] Create/activate the documented Python virtual environment.
- [ ] Install `requirements.txt`.
- [ ] Keep `PS02_demo_data-20261127T071007Z-1-001.zip` local. Never commit it.
- [ ] Start the nondestructive dataset-demo launcher; do not run a DB-reset script.
- [ ] Select the supplied ZIP in the PS02 Participant Dataset page.
- [ ] Run preflight and review errors / warnings.
- [ ] Run dry-run and inspect actual runtime totals.
- [ ] Import once and note batch ID / row totals.
- [ ] Import again to verify idempotence (no doubled totals).
- [ ] Check the charts are computed from the participant batch and carry source labels.
- [ ] Check legacy pages still load and synthetic features are clearly marked synthetic.
- [ ] Check no raw text, author names, handles, phone/payment IDs or exact personal details are exposed in UI, logs or screenshots.
- [ ] Capture screenshots of preflight, aggregate insights and provenance.
- [ ] Rehearse the narrative below.

## Judge narrative (3–4 minutes)
1. “The committee provided a multi-platform dataset. We made the existing platform ingest and validate that exact dataset reproducibly.”
2. Select the ZIP and show computed file inventory / schema validation.
3. Show real aggregate counts, platforms, IST timeline, attachments and data-quality findings.
4. Show import batch provenance and the idempotent second run.
5. Show a legacy feature only on separately labelled synthetic demo data.
6. Explain: hash manifest confirms file-byte consistency, not factual truth; model flags are not ground truth; no judge answer key is supplied in participant data.

## Do not
- Show any personal identifier, author or raw post content.
- Claim a person is guilty or that a model identified a real-world perpetrator.
- Claim synthetic benchmark scores are accuracy on participant data.
- Say that judge answer labels exist if they are not present.
- Blend synthetic replay with committee-provided data.
- Click any destructive reset action.
- Claim live ingestion if the screen is replaying synthetic data.
- Stage dataset ZIP, extracted source files, raw reports or participant DB for Git commit.
