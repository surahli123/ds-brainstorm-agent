# Handover: DS AutoResearch v2 — Feedback-Forward + Binary Eval

**Date:** 2026-03-25
**Project:** ds-brainstorm-agent (`/Users/surahli/Documents/projects/ds-brainstorm-agent`)
**Branch:** main (PRs #2 and #3 merged)

## Last Session Summary

Full implementation session: built v1 autoresearch loop (PR #2), ran live 10-cycle test on synthetic draft (4.72 → 5.87, +24%), then built v2 features — feedback-forward and binary eval scoring (PR #3). Both merged. TDD throughout, 3 code reviews, 1 security review, all findings fixed.

## Current State

- **47/47 tests passing**
- v1 loop: working end-to-end (Claude Code writer + Codex judges)
- v2 feedback-forward: wired into loop, writer gets full judge critiques
- v2 binary eval: scoring functions + templates ready, format-agnostic pipeline
- Pre-commit hook installed blocking commits to main
- CLAUDE.md updated with worktree isolation + CLI validation rules

## Live Test Results (v1, synthetic draft)

Baseline 4.72 → Final 5.87 (+24%). Plateaued after 1 kept edit (exec summary rewrite). Root cause: substance weaknesses require new data the writer can't fabricate. Feedback-forward should help the writer make more targeted edits in v2 runs.

## Next Steps

1. **Live test with feedback-forward** — Re-run 10 cycles on synthetic draft to see if the writer makes more targeted improvements now that it receives judge critiques. This is the key validation of v2.

2. **Test binary judge templates** — Run with `substance-judge-binary.md` / `communication-judge-binary.md` to compare scoring stability vs the 1-10 templates. Need to add a `--judge-mode binary` flag or template selection mechanism.

3. **Lower threshold or add 3-run averaging** — v1 test showed 0.3 threshold rejected real +0.21/+0.24 improvements. Consider lowering to 0.15 or adding `--runs 3`.

4. **Test on a real analysis draft** — Synthetic test validated infrastructure. Real test would validate judge quality on actual DS work.

5. **Phase-skip for early cycles** — Let writer target weakest dimension regardless of phase assignment. In v1 test, all cycles were "structural" while substance was the bottleneck.

## Key Context

- **Architecture:** Claude Code CLI writes (default), Codex CLI judges (parallel), external orchestrator (`loop_runner.py`), git keep/revert in temp dir
- **Binary templates exist but no toggle mechanism yet** — currently hardcoded to `substance-judge.md` / `communication-judge.md` in `call_codex_judge()`. Need a flag or config option to switch to binary templates.
- **Global pre-commit hook** at `~/.git-hooks/pre-commit` blocks commits to main/master
- **Worktree isolation rule** — all reviewer/explorer subagents must use `isolation: "worktree"`

## Relevant Files

1. `loop_runner.py` — orchestrator (920 lines)
2. `evaluate.py` — Codex judges + binary scoring (400 lines)
3. `test_smoke.py` — 47 tests
4. `program.md` — single-cycle writer prompt with feedback-forward guidance
5. `review_config.yaml` — rubric weights + thresholds
6. `skills/ds-autoresearch/references/` — judge templates (4 files: 2 numeric + 2 binary)
7. `runs/20260324-223249/` — v1 10-cycle test artifacts (scores, critiques, diffs)
8. `dev/sessions/2026-03-24-ds-autoresearch-v1-implementation.md` — full implementation handover

## Pickup Prompt

```
Read these files first:
1. /Users/surahli/Documents/projects/ds-brainstorm-agent/CLAUDE.md
2. /Users/surahli/Documents/projects/ds-brainstorm-agent/docs/handover-2026-03-25-v2-feedback-binary.md

DS AutoResearch v1+v2 shipped (PRs #2, #3 merged). 47 tests pass.
v2 added feedback-forward (judge critiques → writer) and binary eval scoring.
Neither has been live-tested yet — that's the priority.

Next: run live test with feedback-forward to validate v2 effectiveness.
```
