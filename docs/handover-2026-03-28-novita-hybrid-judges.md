# Handover: DS AutoResearch v1.4 — Novita Provider + Hybrid Judges

**Date:** 2026-03-28
**Project:** ds-brainstorm-agent
**Branch:** `feature/ds-autoresearch-v2-feedback-forward`
**Commit:** `c780d8a`

## Last Session Summary

Full build-test-reflect cycle. Browsed eBay marketing takehome slides, converted to markdown, manually improved (+1.53 composite), then built automated loop infrastructure. Added Novita AI as writer/judge provider, auto-approve flag, multi-run judge averaging, live dashboard. Ran the loop successfully: 6.10 → 7.77 (+27%) in 5 automated cycles. Validated binary judges (found them noisy — stdev 0.507), designed hybrid scoring instead. Ran /office-hours + /plan-eng-review on the v2 design doc. Implemented all eng review fixes. 65/65 tests.

## Current State

**Working:**
- Novita writer: DeepSeek V3.2, MiniMax M2.7, GLM-4.7-Flash via `--provider novita`
- Novita judges: `--judge-provider novita --judge-model minimax/minimax-m2.7`
- Auto-approve: `--auto-approve` skips human gate
- Multi-run averaging: `--runs 3` with first-run score reuse
- Hybrid judge templates: written but not yet tested end-to-end
- Human pause: prints actionable gaps at plateau
- Dashboard: Chart.js step chart + bar chart at http://localhost:8765/dashboard.html
- 65/65 tests passing

**Not yet validated:**
- Hybrid composite calibration (does hybrid produce comparable scores to pure numeric?)
- RovoDev server mode provider (designed, not implemented)
- RovoDev skill packaging

## Next Steps (Priority Order)

### 1. Validate hybrid composite calibration
Run `--judge-format hybrid` on the eBay analysis and compare composite to `--judge-format numeric`. If binary dims inflate the composite, adjust dimension weights in `review_config.yaml`.

```bash
cd /Users/surahli/Documents/projects/ds-brainstorm-agent
python3 evaluate.py --file ebay_marketing_analysis.md  # numeric baseline
# Then set hybrid and re-run:
python3 -c "
import evaluate
evaluate.set_judge_format('hybrid')
evaluate.set_judge_provider('novita', 'minimax/minimax-m2.7')
# ... run evaluation
"
```

### 2. Run full loop with hybrid judges
```bash
python3 loop_runner.py --input ebay_marketing_analysis_original.md --cycles 10 \
  --provider novita --judge-provider novita --judge-model minimax/minimax-m2.7 \
  --judge-format hybrid --auto-approve --keep-workdir
```

### 3. Build RovoDev server mode provider
- `call_writer_rovodev()` and `call_rovodev_judge()` — POST to `http://localhost:<port>/v3/set_chat_message`, stream via SSE
- `--provider rovodev --rovodev-port 8123`
- Requires `acli rovodev serve 8123` running separately
- Socket timeout: 5 min

### 4. Package as RovoDev skill
- Adapt SKILL.md for `.rovodev/skills/ds-autoresearch/` format
- Copy hybrid templates to references/
- Test with team

### 5. Commit uncommitted test artifacts
The `ebay_marketing_analysis_original.md` and `runs/` directories are test artifacts. Decide whether to track or gitignore.

## Key Decisions Made This Session

| # | Decision | Choice | Why |
|---|----------|--------|-----|
| 1 | Writer provider | Novita API (DeepSeek V3.2) | Cheapest strong model, OpenAI-compatible |
| 2 | Judge scoring | Hybrid (binary+numeric) | Binary stdev 0.0 for objective, numeric+avg for subjective |
| 3 | Auto-approve | --auto-approve flag | Human gate blocks automated runs |
| 4 | Template design | Mixed templates (2 calls) | Half the API cost vs split templates (4 calls) |
| 5 | Company deployment | RovoDev server mode | 256-char run limit kills direct CLI, SSE streaming needed |
| 6 | Model config (company) | Opus 4.6 writer + GPT 5.4 judge | Cross-model independence, medium effort on judge |
| 7 | Cycle eval DRY | Reuse first run scores | Saves N+2 → N judge calls per cycle |

## Key Files

1. `loop_runner.py` (1123 lines) — main orchestrator with all providers
2. `evaluate.py` (549 lines) — judge interface with format routing
3. `review_config.yaml` — weights, dimension_format, thresholds
4. `test_smoke.py` (963 lines) — 65 tests
5. `dashboard.html` — Chart.js live dashboard
6. `skills/ds-autoresearch/references/*-hybrid.md` — hybrid judge templates
7. Design doc: `~/.gstack/projects/surahli123-ds-brainstorm-agent/surahli-feature/ds-autoresearch-v2-feedback-forward-design-20260328-101500.md`

## Critical Finding: Judge Noise Data

Same document scored across methods:

| Method | Stdev | Suitable for |
|--------|-------|-------------|
| Numeric single-run | ~0.75 | Nothing (too noisy) |
| Numeric 3-run avg | ~0.20 | Relative (keep/revert) |
| Binary single-run | 0.507 | Nothing (worse than expected) |
| Binary per-dim (objective) | 0.000 | Absolute thresholds |
| Binary per-dim (subjective) | 1.1-2.2 | Nothing (very noisy) |
| **Hybrid (proposed)** | **TBD** | **Needs validation** |

## DS Interview Prep Learnings

Saved to memory: 7 high-leverage patterns for DS takehome write-ups. The biggest: lead with the answer (exec summary), acknowledge what you can't prove (caveats), be precise about what you did (exact dates, correct terminology). See `memory/user_ds_interview_writing_patterns.md`.
