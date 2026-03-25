# Handover: DS AutoResearch v1 — Implementation + Live Test

**Date:** 2026-03-24
**Project:** ds-brainstorm-agent (`/Users/surahli/Documents/projects/ds-brainstorm-agent`)
**Branch:** `feature/ds-autoresearch-v1`
**PR:** https://github.com/surahli123/ds-brainstorm-agent/pull/2

## What Was Done

Built and shipped the DS AutoResearch loop — an automated edit→evaluate→keep/revert system for DS analysis documents. Claude Code writes improvements, Codex CLI judges score them on 8 dimensions, git manages keep/revert in an isolated temp directory.

### Implementation (7 plan steps, all complete)
1. Workspace + branch setup
2. Judge prompt templates (substance + communication)
3. program.md rewritten as single-cycle writer prompt
4. evaluate.py wired with Codex judge calls (parallel via ThreadPoolExecutor)
5. loop_runner.py orchestrator (910 lines)
6. SKILL.md documentation
7. 37 smoke tests (TDD)

### Reviews Passed
- 2 full code reviews (SHIP verdict after fixing all findings)
- 1 security review (3 MEDIUM fixed: git timeout, backup, temp files)
- All 16 eng/CEO review decisions verified

### Live Test Results (Codex Judges on Synthetic Draft)

**Input:** A deliberately weak search relevance analysis (43 lines, missing methodology, vague exec summary, no confidence intervals)

**Baseline scores (composite: 4.58):**

| Dimension | Score | Judge Assessment |
|-----------|-------|-----------------|
| statistical_rigor | 2.5 | "Point estimates without uncertainty or test justification" |
| methodology_soundness | 3.0 | "Method only sketched at a high level — not reproducible" |
| evidence_conclusion_alignment | 4.0 | "Causal statements go beyond the evidence shown" |
| data_interpretation_accuracy | 5.5 | "Does not contradict its own numbers, but interpretation gaps" |
| narrative_flow | 6.0 | "Follows sensible order but story doesn't develop" |
| audience_calibration | 6.5 | "Mixes business framing with unexplained jargon" |
| visualization_effectiveness | 7.0 | "No charts — scored N/A default" |
| executive_summary_clarity | 3.5 | "Says only 'Search relevance went down. We should fix it.'" |

**Cycle progression:**

| Cycle | Phase | Composite | Delta | Decision | What Happened |
|-------|-------|-----------|-------|----------|---------------|
| 0 | baseline | 4.58 | — | — | Weak draft scored correctly low |
| 1 | structural | 5.58 | +1.00 | KEEP | Writer rewrote exec summary → 3.5→8.5 |
| 2 | structural | 5.59 | +0.01 | REVERT | Noise — below 0.3 threshold |
| 3 | substance | 6.37 | +0.79 | REVERT | Human gate fired, no stdin → safe default |

**Final: 4.58 → 5.58** (+1.0 in 1 kept edit, 3 cycles total)

**Key observations:**
- Judges correctly identified every known weakness in the draft
- Substance judge critiques are specific and actionable (quotes exact passages, suggests exact improvements)
- Communication judge caught the audience calibration mismatch and weak exec summary
- Cycle 3 would have been kept (+0.79 real improvement) but human gate reverted because no interactive input was available — correct safe behavior
- Cycle 2 revert was correct: +0.01 is scoring noise, not real improvement

### Bug Fixed During Live Test
- `codex exec` doesn't have `--read` or `-q` flags. Fixed to pass prompt via stdin with `codex exec -s read-only -`. Committed and pushed to PR.

## Current State

- **PR #2** is open, all tests pass, ready to merge
- **Live test artifacts** in `runs/20260324-222309/` (scores, critiques, diffs, summary)
- **Dry run script** `dry_run.py` available for testing without LLM calls
- **Test draft** `test_analysis.md` can be reused

## Lessons Learned (saved to CLAUDE.md + enforced)

- **Subagents can switch branches.** Code-reviewer agents explored git history and switched from feature branch to main. 6 commits landed on wrong branch. Fixed by:
  1. Always use `isolation: "worktree"` for reviewer/explorer agents (CLAUDE.md rule)
  2. Always run `git branch --show-current` before every `git commit` (CLAUDE.md rule)
  3. **Global pre-commit hook** at `~/.git-hooks/pre-commit` blocks commits to main/master (automated enforcement)
- **Validate CLI flags before integration.** `codex exec --read` and `-q` don't exist. Run `<tool> --help` before writing subprocess calls.

## Full 10-Cycle Test Results (Real LLM Calls)

**Input:** Same synthetic search relevance analysis (43 lines, deliberately weak).
**Config:** 10 cycles, Claude Code writer, Codex judges, 0.3 min improvement threshold.
**Human gate:** Auto-approved (non-interactive test run).

### Score Progression

| Cycle | Phase | Composite | Delta | Decision | Key Changes |
|-------|-------|-----------|-------|----------|-------------|
| 0 | baseline | **4.72** | — | — | stat_rigor=3.5, methodology=3.0, exec_summary=3.5 |
| 1 | structural | **5.87** | **+1.15** | **KEEP** | exec_summary 3.5→8.5, evidence_align 4.0→5.0, audience_cal 6.0→7.5 |
| 2 | structural | 6.08 | +0.21 | REVERT | Below 0.3 threshold (likely noise) |
| 3 | structural | 6.11 | +0.24 | REVERT | Below 0.3 threshold |
| 4 | structural | 5.85 | -0.02 | REVERT | Score dropped → **3 consecutive → HALT** |

**Result: 4.72 → 5.87 (+1.15 composite, +24% improvement, 1 kept edit)**

### What the Writer Actually Changed

The single kept edit (cycle 1) rewrote the executive summary from:
> "Search relevance went down in Q1. We should fix it."

To:
> "A February 2026 embedding model update degraded long-tail query relevance (4+ words), dropping NDCG@10 from 0.74 to 0.62 for this segment — a 16% decline affecting the query class most tied to high-intent, conversion-driving searches. Overall NDCG@10 fell from 0.72 to 0.68, CTR dropped from 45% to 41%, and zero-result rate rose 15%. Short queries improved, confirming the regression is isolated to long-tail. We recommend a hybrid routing approach..."

This was the highest-impact single edit possible — the exec summary was scored 3.5 at baseline and jumped to 8.5.

### Why It Plateaued After 1 Edit

**Root cause: the writer can only edit the text, but the substance weaknesses require NEW content that doesn't exist in the draft.**

The remaining low scores are:
- statistical_rigor: 3.5 → 3.5 (never improved) — needs confidence intervals, p-values, sample sizes that the writer can't fabricate
- methodology_soundness: 3.0 → 4.0 (barely improved) — needs methodology details the writer doesn't have
- evidence_conclusion_alignment: 4.0 → 5.0 (modest) — needs actual evidence/experiments

The communication dimensions all jumped to 7.0-8.5 after cycle 1, leaving substance as the bottleneck. But the writer prompt says "NEVER fabricate data, statistics, or citations" — so it correctly refuses to invent confidence intervals or methodology details.

**This is the correct behavior.** The loop maximized what's possible from editorial improvement alone. The remaining gap requires the analyst to add real data.

### Effectiveness Assessment

| Aspect | Rating | Evidence |
|--------|--------|---------|
| **Judge quality** | Strong | Correctly identified every weakness, specific critiques with exact quotes |
| **Writer quality** | Strong | Made the highest-impact edit first, respected constraints |
| **Decision logic** | Working | Kept real improvement, reverted noise, halted on plateau |
| **Threshold (0.3)** | Potentially too aggressive | Cycles 2-3 had real improvements (+0.21, +0.24) but were below threshold. With noise averaging (3-run), these might have been kept |
| **Phase assignment** | Suboptimal | All 4 cycles were "structural" — only cycle 5+ would have been "substance". Loop halted before reaching the phase that targets the real weaknesses |

### Recommendations for v1.1

1. **Feedback-forward is the #1 priority.** The writer doesn't know WHY scores didn't improve. Passing judge critiques ("statistical_rigor is 3.5 because no confidence intervals") would give the writer actionable direction.

2. **Lower threshold to 0.15 or add 3-run averaging.** The 0.3 threshold rejected improvements of 0.21 and 0.24 that were likely real. With 3-run averaging, noise drops and a lower threshold becomes safe.

3. **Consider skipping phase enforcement for early cycles.** The biggest gap is substance (3.5-4.0), not structure (7.0-8.5 after cycle 1). Letting the writer target the weakest dimension regardless of phase could be more effective.

### Run Artifacts

- `runs/20260324-223249/summary.json` — run metadata
- `runs/20260324-223249/scores.jsonl` — per-cycle scores (all dimensions)
- `runs/20260324-223249/critiques/` — 10 judge critique files (substance + communication × 5 evals)
- `runs/20260324-223249/diffs/` — per-cycle diffs
- `runs/20260324-223249/analysis-initial.md` — original 43-line draft
- `runs/20260324-223249/analysis-final.md` — improved version (exec summary rewritten)

## Next Steps (Post-v1)

From the plan, in priority order:

1. **Judge calibration** — Run judges on 10 real drafts, compare scores to human judgment, tune prompts. The live test shows judges are directionally correct but calibration will improve consistency.

2. **Feedback-forward** — Pass judge critique text to the next writer cycle. Currently the writer gets a score summary but not the detailed critique. The critiques are saved to `critiques/` — they just need to be fed to the writer prompt.

3. **3-run averaging** — Reduce scoring noise (cycle 2's +0.01 was likely noise). Add `--runs 3` to average scores. Infrastructure exists in `evaluate_with_averaging()`.

4. **Pipeline integration** — Connect ds-report-gen output as input source.

5. **Editorial simulator** — Stakeholder reader simulators (from build-stakeholder-profile) for decision-quality scoring.

## Pickup Prompt (for parallel session)

```
Read the project context:
1. /Users/surahli/Documents/projects/ds-brainstorm-agent/CLAUDE.md
2. /Users/surahli/Documents/projects/ds-brainstorm-agent/dev/sessions/2026-03-24-ds-autoresearch-v1-implementation.md

Branch: feature/ds-autoresearch-v1
PR: https://github.com/surahli123/ds-brainstorm-agent/pull/2

The DS AutoResearch loop is implemented and live-tested. The PR is ready to merge.
Codex judges work correctly — verified with a live 3-cycle test on a synthetic
search relevance analysis.

Key files:
- loop_runner.py — orchestrator (910 lines)
- evaluate.py — Codex judge calls + scoring
- test_smoke.py — 37 tests (all pass)
- program.md — single-cycle writer prompt
- review_config.yaml — rubric weights + thresholds
- skills/ds-autoresearch/ — SKILL.md + judge templates
- runs/20260324-222309/ — live test output (scores, critiques, diffs)

Next priority: [STATE WHAT YOU WANT THE SESSION TO DO]
Options:
- Merge PR #2 and start judge calibration (run on 10 real drafts)
- Add feedback-forward (pass judge critiques to writer)
- Add 3-run averaging to reduce scoring noise
- Run a full 10-cycle test on a real analysis draft
```
