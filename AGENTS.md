# Agent instructions

Read `ANTIGRAVITY_HANDOFF.md` before doing implementation work.

This is the existing Telegram & Social Media PS02 hackathon project. The root README is stale and mismatched; verify actual source, entry point and docs. Do not replace it with an unrelated project or rewrite from scratch.

Priority: make the committee-provided participant ZIP a real, reproducible demo path in the existing app: safe ZIP validation, Telegram JSON/social CSV parsing, dry-run, isolated/idempotent import, aggregate analytics, provenance, tests and a nondestructive launch command.

Do not pass participant data into the legacy worker's personal/payment identifier extraction or cross-platform profiling path. Keep the participant demo aggregate-only. Do not expose raw post text, authors, handles, phone/payment IDs, wallets or other personal identifiers. Do not target people, build dossiers, infer guilt, join private groups, DM, scrape members, train models on participant data or send participant content to external services.

Never commit the ZIP, extracted participant files, raw records or participant DB. Do not reset the existing `data/osint_monitor.db` by default. Preserve old pages and synthetic features, clearly labelled. Run actual tests; never report unverified success. Do not force-push or merge into main without explicit owner approval.
