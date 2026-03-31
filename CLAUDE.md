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

### Hybrid Scoring (validated 2026-03-28)
- **Binary checkpoints** for objective dimensions: `statistical_rigor` (stdev 0.000), `data_interpretation_accuracy` (stdev 0.000)
- **Numeric 1-10** for subjective dimensions: `methodology_soundness`, `evidence_conclusion_alignment`, `narrative_flow`, `audience_calibration`, `visualization_effectiveness`, `executive_summary_clarity`
- Config: `dimension_format` in `autoresearch/review_config.yaml`
- Templates: `autoresearch/judges/*-hybrid.md`

### Providers
| Environment | Writer | Judge | Transport |
|-------------|--------|-------|-----------|
| Personal | DeepSeek V3.2 via Novita | MiniMax M2.7 via Novita | HTTP API |
| Company | Opus 4.6 via RovoDev | GPT 5.4 via RovoDev | Native subagent dispatch |
| Default | Claude Code CLI | Codex CLI | Subprocess |

### Validated Results
- Full loop: 6.10 → 7.77 (+27%) in 5 automated cycles (numeric judges)
- Hybrid calibration: no inflation (7.02 vs 7.41, weights unchanged)
- Content ceiling: ~7.5 (writing-limited, not substance-limited)
- Binary stdev: 0.000 (objective), 1.1-2.2 (subjective) — hybrid solves this

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
- **Multi-run averaging (--runs 3) for numeric dimensions.** Single-run stdev ~0.75. Three-run stdev ~0.20. Binary dimensions don't need averaging.

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
