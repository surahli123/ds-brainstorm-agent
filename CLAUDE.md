# DS Brainstorm Agent

Two tools for data scientists: **Brainstorm** (plan analyses) and **AutoResearch** (polish write-ups).

## Project Structure (restructured 2026-03-28)

```
autoresearch/          # Karpathy-style improvement loop
  loop_runner.py       #   Python orchestrator (Novita/Anthropic/Claude Code)
  evaluate.py          #   Judge harness with hybrid format routing
  judges/              #   Judge prompt templates (numeric/binary/hybrid)
  program.md           #   Writer system prompt
  review_config.yaml   #   Scoring weights, thresholds, dimension_format
  calibrate_hybrid.py  #   Compare numeric vs hybrid scoring
  dashboard.html       #   Chart.js live dashboard
  SKILL.md             #   Claude Code skill wrapper

brainstorm/            # Socratic multi-persona debate
  skill/               #   ds-brainstorm skill (orchestrator + 3 personas)
  report-gen/          #   ds-report-gen skill
  stakeholder-profiles/ #  build-stakeholder-profile skill

rovodev-skill/         # RovoDev deployment (pure markdown, no Python)
  skills/              #   Orchestrator skill
  subagents/           #   Writer + 2 judge subagents (5 refs each)

tests/                 # 70 unit tests
examples/              # Sample analyses
```

## AutoResearch — Architecture

### Loop Design
- **Writer** (Model A) makes ONE focused improvement per cycle
- **Judges** (Model B, x2) score substance + communication
- **Keep/revert** based on composite delta (threshold: 0.3)
- **Feedback-forward:** judge critiques passed to writer each cycle
- **Plateau detection:** 3 consecutive reverts → print actionable gaps + halt

### Hybrid Scoring (validated 2026-03-30)
- **Binary checkpoints** for objective dimensions: `statistical_rigor` (stdev 0.000), `data_interpretation_accuracy` (mostly stable, occasional 7.5↔8.33)
- **Numeric 1-10** for subjective dimensions: `methodology_soundness`, `evidence_conclusion_alignment`, `narrative_flow`, `audience_calibration`, `visualization_effectiveness`, `executive_summary_clarity`
- **`--runs 3` required for reproducibility.** Single-shot (`--runs 1`) produces ~1-point baseline swings. With 3-run averaging: hybrid stdev 0.16, numeric stdev 0.36
- Config: `dimension_format` in `autoresearch/review_config.yaml`
- Templates: `autoresearch/judges/*-hybrid.md`

### Providers
| Environment | Writer | Judge | Transport |
|-------------|--------|-------|-----------|
| Personal | DeepSeek V3.2 via Novita | MiniMax M2.7 via Novita | HTTP API |
| Company | Opus 4.6 via RovoDev | GPT 5.4 via RovoDev | Native subagent dispatch |
| Default | Claude Code CLI | Codex CLI | Subprocess |

### Validated Results
- **Numeric loop (`--runs 1`):** 6.10 → 7.77 (+27%) in 5 cycles — but 6.10 baseline was a single-shot outlier (averaged numeric baseline = 7.52). True improvement ~+0.25, rest is noise recovery
- **Hybrid loop (`--runs 3`):** 7.21 → 7.21 (plateau, 0/3 kept) — correctly identifies document is at content ceiling
- **Hybrid reproducibility:** stdev 0.16 with `--runs 3` (2.25x tighter than numeric's 0.36). Range 0.38 across 5 calibration runs
- **Calibration:** hybrid mean 7.24 vs numeric mean 7.52 (same model, different rubric interpretation). Weights unchanged
- **Content ceiling:** ~7.2 (hybrid) / ~7.5 (numeric). Writing-limited, not substance-limited. Gaps: effect sizes, methodology depth, visualization quality
- **Always use `--runs 3`** for any scored comparison. Single-shot scoring is unreliable for keep/revert decisions

## Brainstorm — Architecture

### Personas (parallel subagent dispatch)
| Persona | Role | Challenges |
|---------|------|-----------|
| Methodology Critic | Analytical rigor | Confounders, statistical methods, sample sizes |
| Stakeholder Advocate | Business impact | Framing for execs, metrics that matter |
| Pragmatist | Feasibility | Data availability, timeline, scope |

### Flow
1. Scope check (reject multi-topic)
2. Search grounding (web search for domain context)
3. Parallel subagent dispatch (3 personas)
4. Cross-persona synthesis
5. Socratic dialogue loop (max 3 rounds)
6. Structured JSON output → consumed by report-gen

### Graceful Degradation
- Level 0: Full (search + parallel subagents)
- Level 1: No WebSearch (domain + user context only)
- Level 2: No subagents (single-agent inline, all 3 perspectives)
- Level 3: Minimal (user-context-only brainstorm)

## Hard Rules

- **Run `cd autoresearch/` before `python3 loop_runner.py`** — imports resolve relative to script location
- **Judge templates live in `autoresearch/judges/`** — evaluate.py's `JUDGE_TEMPLATES_DIR` points here
- **Tests run from repo root:** `python3 -m pytest tests/ -q` — conftest.py adds autoresearch/ to sys.path
- **Stakeholder profiles are gitignored** — `stakeholders/` contains personal data, never commit
- **Dev artifacts are gitignored** — `dev/`, `docs/handover-*`, `runs/`, `*.bak`, `eval_log.jsonl`

## Strategies

- **Validate eval assumptions with data before building.** Run 5 evals, measure stdev. Binary judges measured 0.507 stdev (worse than expected) — led to hybrid design.
- **Use native agent capabilities over API wrappers.** RovoDev subagent dispatch eliminated the entire server-mode provider. If the agent can dispatch subagents, don't build HTTP clients.
- **Human pause at plateau > full automation.** The loop can't add substance that doesn't exist. Print actionable gaps and let the human add content.
- **Cross-model independence for writer/judge.** Same model judging its own output is unreliable. Use different models (or at minimum, different temperature).
- **Multi-run averaging (--runs 3) is mandatory for all scored runs.** Single-shot produces ~1-point baseline swings. With `--runs 3`: hybrid stdev 0.16, numeric stdev 0.36. Without averaging, keep/revert decisions are noise-driven.
- **Beware regression-to-mean in improvement claims.** A low single-shot baseline inflates apparent improvement. The numeric +1.67 was mostly noise recovery (true improvement ~+0.25). Always compare against averaged baselines.

## Anti-Patterns

- **Don't assume binary = stable.** Binary checkpoints are only stable for objectively verifiable questions ("Are CIs reported?"). Subjective questions ("Do conclusions trace to evidence?") have stdev >1.0 even with binary format.
- **Don't build API providers when the agent has native dispatch.** The RovoDev server mode provider was designed, eng-reviewed, and then eliminated by one user question.
- **Don't run the loop on already-improved documents.** The content ceiling means re-running on an improved doc plateaus immediately. Use a fresh draft.
- **Don't compare scores across judge models.** DeepSeek scores higher than MiniMax. Pick one model for consistent tracking.

## Pickup Instructions

Every session start:
1. Read this CLAUDE.md
2. Check `docs/handover-*` for latest session context (gitignored locally, not in repo)
3. Run `python3 -m pytest tests/ -q` to verify nothing is broken

## Session End Protocol

Before ending every session:
1. Update CHANGELOG.md if anything shipped
2. Write handover doc to `docs/handover-YYYY-MM-DD-<topic>.md`
3. Update memory files in `~/.claude/projects/*/memory/`

## Domain Context: ACTIVE

Search relevance and DS expertise applies. Domain knowledge for search-relevance seeded in `brainstorm/skill/references/search-relevance.md`.
