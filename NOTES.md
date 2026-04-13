# Brígh Notes

Last updated: 2026-04-13

## Decision Log

1. Build Phase 1 first, BrighAI later.
Why:
- You explicitly said AI comes later.
- It keeps scope focused on delivering a working core product first.

2. Implement in this order: scanner -> detectors -> generator -> CLI verification.
Why:
- Scanner/detection are the foundation for useful outputs.
- Verifying CLI last confirms full end-to-end flow.

3. Keep `CLAUDE.md` as generated output, not a manual progress doc.
Why:
- `brigh scan` regenerates `CLAUDE.md`, so manual notes there will be overwritten.
- Persistent project progress belongs in separate docs.

4. Add a persistent status file (`STATUS.md`).
Why:
- You asked for ongoing progress tracking.
- `STATUS.md` avoids losing updates during scans.

5. Improve scanner config detection to support nested paths (for example `supabase/config.toml`).
Why:
- Some configs are identified by relative path, not just filename.
- Without this, backend/infrastructure detection misses real project signals.

6. Parse Python dependencies from `pyproject.toml` (PEP 621 + Poetry) in addition to `requirements.txt`.
Why:
- Many modern Python projects use `pyproject.toml` as the primary dependency source.
- Better dependency input improves framework/backend/database/testing detection accuracy.

7. Merge Python dependency sources before running detectors.
Why:
- Projects may define dependencies across multiple files.
- Combined input reduces false negatives in detection.

8. Harden generator target handling (validate unknown targets, deterministic ordering, dedupe).
Why:
- Safer behavior for CLI usage and automation.
- Deterministic output is easier to test and reason about.

9. Add regression tests before moving on.
Why:
- Prevents accidental breakage while iterating quickly.
- Locks in current Phase 1 behavior.

10. Add CI to run tests and a CLI smoke check.
Why:
- Keeps quality checks automatic on pushes/PRs.
- Confirms both logic and actual CLI entrypoint behavior continuously.

11. Mark Phase 1 roadmap items as complete in `README.md`.
Why:
- Documentation should match delivered functionality.
- Makes current project maturity clear to contributors/users.
