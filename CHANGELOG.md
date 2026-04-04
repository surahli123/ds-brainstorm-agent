# Changelog

## [1.8.0] - 2026-04-03 — Domain Expert Persona, Search Skills Eval Framework

### Added
- 4th persona: Domain Expert — activated by `--domain`, challenges domain validity with established frameworks and benchmarks
- Domain Challenge Patterns section (§ 9) in search-relevance.md — 7 search-specific challenge patterns (BEIR/MTEB benchmarks, information need model, retrieval vs extractability, query distribution shift, positional metric transfer, skill vs trajectory eval, judge calibration transfer)
- Conditional 4th dispatch in SKILL.md Phase 1 (fires only when `--domain` specified)
- Phase 2 synthesis updated with Domain Expert tensions (domain vs methodology, domain vs feasibility)
- 10 new brainstorm tests (61 brainstorm total, 151 full suite)
- Search Skills evaluation framework document (docs/search-skills-eval-framework.md)

### Validated
- `--knowledge-dir` tested with Search Metric Analyzer knowledge files (6 YAML files) — summaries loaded correctly, all 3 personas cited specific baselines and failure modes from knowledge files
- Brainstorm run on "How to evaluate Search Skills in Agentic Search" confirmed domain expertise gap: personas challenged methodology/business/feasibility but missed IR-specific concerns (BEIR, information need model, answer extractability)
- Eng reviewed as Search IC9: 3 architecture decisions (challenge patterns in domain file, --domain-only trigger, accept compute cost)

### Design Decisions
- Challenge patterns live in domain files (not persona file) — adding domain expertise is "add patterns to your .md", no code changes per domain
- Domain Expert fires only with `--domain` (not `--knowledge-dir` alone) — knowledge files provide data but not reasoning frameworks
- Accepted ~33% compute increase when `--domain` used — users opting into domain depth expect thoroughness
- Persona uncertainty type: domain validity (distinct from statistical/value/feasibility)

### Context
- Baidu "Agentic Search" paper (CCIR 2026) provided key context: Search Skills architecture, PRM+ORM reward design, multi-agent listwise inspection
- Search Skills eval framework proposes 3 failure classes: recall failure, precision failure, trust failure (silent killer unique to agentic search)

## [1.7.0] - 2026-04-02 — Targeted Adversarial Pushback, Verdict Assessment, Eval-001 Validated

### Added
- Step 3.2 upgraded to "Targeted Adversarial" — Socratic pushback requires verbatim quotes from persona `findings[].description` with domain_reference attribution (PR #13)
- Step 2.5.1 "Verdict Assessment" — informational banner after synthesis when all non-error personas return MAJOR_ISSUES unanimously, with concrete options: continue, narrow scope, add context (PR #13)
- 12 new brainstorm skill structural tests (51 brainstorm total, 124 full suite) (PR #13)

### Validated
- Eval-001 with REAL parallel subagent dispatch: weighted average 4.50/5.0 (PASS)
- D1 (Perspective Independence): 5.0 vs 4.85 inline baseline (+0.15, no degradation from parallel dispatch)
- system_understanding populated in all 3 persona outputs
- MANDATORY FIRST ACTIONS executed with distinct starting behaviors per persona
- PROHIBITED CONVERGENCE prevented lane drift across all 3 personas
- Eng reviewed with outside voice (Claude subagent): 10 findings, 3 cross-model tensions resolved

### Design Decisions
- Fork Routing (#3) dropped — confirmed as no-op (already implemented in Phase 0→1 flow)
- Option B (orchestrator pushback) over Option A (full Round 2 dispatch) — divergence already solved by PR #12
- Unanimous MAJOR_ISSUES trigger (not any-single) — adversarial calibration makes single-persona trigger fire ~80% of runs
- Post-synthesis mailbox placement — outside voice caught: user needs to see concerns before deciding

## [1.6.0] - 2026-04-02 — Hybrid Reproducibility, Persona Grounding, Knowledge Integration

### Added
- Persona grounding step (Step 2.5): personas must state system understanding before challenging (PR #12)
- Mandatory divergence anchors + prohibited convergence rules per persona with binary litmus tests (PR #12)
- `--knowledge-dir` flag for external domain knowledge loading (e.g., Search Metric Analyzer YAML files) (PR #12)
- Confluence MCP search placeholder — detection, CQL queries, graceful skip (PR #12)
- Context trimming (Step 2.6) between Phase 2 synthesis and Phase 3 Socratic loop (PR #12)
- `system_understanding` field in all persona output schemas and eval structural checks (PR #12)
- 39 new brainstorm skill structural tests (`tests/test_brainstorm_skill.py`) (PR #12)
- Inline dispatch prompts synced with grounding/divergence instructions (PR #12)

### Changed
- CLAUDE.md validated results updated: hybrid `--runs 3` stdev 0.16 (2.25x tighter than numeric), numeric +1.67 improvement was mostly regression-to-mean (PR #10)
- Evidence block reordered: Confluence > External Knowledge > Domain > Web Search (PR #12)
- Convergence rules use binary litmus tests instead of vague ">50% overlap" thresholds (PR #12)
- `--runs 3` documented as mandatory for all scored comparisons (PR #10)

### Validated
- Hybrid reproducibility: stdev 0.16 with `--runs 3` (5 calibration runs × 3 eval-runs)
- Hybrid loop: baseline 7.21, plateau at content ceiling (correctly identifies no improvement possible)
- Numeric benchmark reanalysis: true improvement ~+0.25, not +1.67 (regression-to-mean from single-shot outlier)
- 107 tests passing (39 brainstorm skill + 68 autoresearch)

### Removed
- Stale branch `feature/ds-autoresearch-v2-feedback-forward` (already merged, behind main)

## [1.5.0] - 2026-03-30 — Repo Restructure, RovoDev Skill, DRY Fix

### Changed
- Restructured repo into `autoresearch/` (loop engine) and `brainstorm/` (Socratic debate) modules
- Judge templates moved to `autoresearch/judges/`
- Tests moved to `tests/` with `conftest.py` for path resolution
- Example analyses moved to `examples/`
- Extracted `_average_results()` from duplicated baseline + cycle averaging logic (-20 lines)
- Rewrote CLAUDE.md for restructured paths, added strategies and anti-patterns from session learnings

### Added
- RovoDev pure-skill deployment: `rovodev-skill/` with orchestrator + writer + 2 judge subagents (5 per-dimension reference files each)
- Polished README covering both tools, CLI reference, scoring dimensions, supported models
- `tests/conftest.py` for sys.path resolution after restructure
- 3 new tests (73 total)

### Removed
- Dev artifacts from tracking: session logs, handover docs, design specs, personal commands
- Unrelated commands from `.claude/commands/`

### Validated
- Hybrid loop end-to-end: runs without errors, hybrid judges produce correct binary + numeric scores
- Hybrid calibration: no composite inflation (7.02 hybrid vs 7.41 numeric)
- CLI invocation from `autoresearch/` directory verified

## [1.4.0] - 2026-03-28 — Novita Provider, Hybrid Judges, Auto-Approve

### Added
- Novita AI writer provider (`--provider novita`), supports DeepSeek V3.2, MiniMax M2.7, GLM-4.7-Flash
- Novita AI judge provider (`--judge-provider novita --judge-model`)
- Auto-approve flag (`--auto-approve`) skips human gate for marginal improvements
- Multi-run judge averaging (`--runs N`) with first-run score reuse (N-1 additional calls, not N+2)
- Hybrid judge format (`--judge-format hybrid`) — binary for objective dims (stdev 0.0), numeric for subjective
- Mixed-format judge templates: `substance-judge-hybrid.md`, `communication-judge-hybrid.md`
- `dimension_format` config in `review_config.yaml` maps each dimension to binary/numeric
- Human pause at plateau — prints actionable gaps from judge critiques instead of just halting
- Live dashboard (`dashboard.html`) with Chart.js step chart, bar chart, dimension bars
- Hybrid calibration utility (`calibrate_hybrid.py`) to compare numeric vs hybrid judges and recommend binary-weight scaling
- 18 new tests (65 total): provider routing, auto-approve, hybrid parsing, mocked API calls

### Changed
- `--model` default is now None (auto-selects per provider: deepseek/deepseek-v3.2 for novita, claude-sonnet for anthropic)
- Git init in temp workdir uses `autoresearch` branch (avoids global pre-commit hook blocking main)
- `evaluate_with_averaging` routes through `_call_judge` (supports novita + codex)
- `call_judges_parallel` routes through `_get_template_name` (supports numeric/binary/hybrid)
- Cycle evaluation reuses first judge run scores (fixes DRY violation — N-1 calls instead of N+2)
- Dependency validation checks judge provider requirements (novita needs NOVITA_API_KEY + openai package)

### Validated
- Full loop run on eBay marketing analysis: 6.10 → 7.77 (+27%) in 5 automated cycles
- Binary judge stdev: 0.507 (worse than numeric 3-run avg at 0.20) — led to hybrid design
- Per-dimension binary stability: statistical_rigor stdev 0.000, evidence_conclusion stdev 2.236
- Plateau confirmed at ~7.5 (content ceiling, not writing ceiling)
- Calibration helper tests: 5 added, suite now 70 passing locally

## [1.3.0] - 2026-03-25 — Feedback-Forward + Binary Eval (v2)

### Added
- Feedback-forward: judge critiques passed to writer via JUDGE FEEDBACK section
  - Writer now knows WHY scores are low, targets specific weaknesses
  - Full critique from previous cycle included in writer prompt
- Binary eval scoring mode
  - `convert_binary_to_numeric()` and `parse_binary_judge_output()` in evaluate.py
  - Binary judge templates: 16 yes/no questions per judge (substance + communication)
  - Score = (true answers / total) × 10 — more stable than 1-10 subjective
  - Transparent format detection: numeric and binary judges work interchangeably
- 10 new tests (47 total): feedback-forward assembly + binary scoring math
- Global pre-commit hook (`~/.git-hooks/pre-commit`) blocks commits to main/master

### Changed
- `_run_codex_with_retry` uses `parse_binary_judge_output` for format-agnostic score extraction
- Cycle summary no longer duplicates critique text (full critiques go via judge_feedback)
- Writer function signatures accept `judge_feedback` param (backward-compatible)

### Fixed
- Codex CLI invocation: `codex exec -s read-only -` via stdin (not `--read` flag)

## [1.2.0] - 2026-03-24 — DS AutoResearch Loop (v1)

### Added
- Automated analysis improvement loop (`loop_runner.py`)
  - Claude Code writes improvements, Codex CLI judges score them
  - Git-based keep/revert in isolated temp directory
  - Percentage-based phases: structural (40%) → substance (40%) → polish (20%)
  - Human gate for marginal improvements (0.3-1.0 range)
  - Stop rules: 3 non-improving cycles, budget cap, target score
  - Backup original before modification, conditional write-back
- Dual Codex judge system (`evaluate.py`)
  - Substance judge: statistical rigor, methodology, evidence-conclusion alignment, data interpretation
  - Communication judge: narrative flow, audience calibration, visualization effectiveness, exec summary
  - Parallel execution via ThreadPoolExecutor
  - Temp directory cleanup, retry-once on malformed output
- Judge prompt templates (`skills/ds-autoresearch/references/`)
  - Full rubric with scoring anchors from review_config.yaml
  - Strict JSON output format with critique field
- Single-cycle writer prompt (`program.md` rewritten)
  - Stripped loop/eval/revert logic (orchestrator handles that)
  - Cycle summary context from previous iterations
  - Writer refusal detection (headers, length, prefix checks)
- Smoke tests (`test_smoke.py` — 37 tests)
  - Decision logic: keep, revert, human gate, regression blocking
  - Stop rules, budget cap, judge failure handling, phase detection
  - Writer output validation, config validation, cycle summary builder
- Skill documentation (`skills/ds-autoresearch/SKILL.md`)

### Changed
- `review_config.yaml`: min_improvement 0.02 → 0.3, max_consecutive_reverts 5 → 3
- `evaluate.py`: wired Codex judge calls, added config weight validation, null-safety

## [1.1.1] - 2026-03-23 — Domain Knowledge Enrichment

### Changed
- Search-relevance domain file expanded from 101 → 227 lines
  - Added metric formulas, baselines, alert thresholds (QSR, DLCTR)
  - Added 9 co-movement diagnostic patterns
  - Added LLM-as-Judge methodology (UMBRELLA + pairwise) with 4 measurement pitfalls
  - Added 8-stage pipeline architecture with per-stage failure modes
  - Added 9-class failure taxonomy with metric signatures
  - Added 4 known recurring patterns and investigation priority order
  - Source: Search Metric Analyzer knowledge base (metric_definitions.yaml, evaluation_methods.yaml, etc.)

## [1.1.0] - 2026-03-22 — Parallel Dispatch, Multi-Stakeholder, Quality Evals, Report Gen

### Added
- Parallel subagent dispatch (Phase 1 default)
  - All 3 personas dispatched in single message for ~3x speedup
  - Graceful degradation: parallel → sequential → single-agent inline
  - Auto-detection of environment capabilities (no config needed)
- Multi-stakeholder support (`--stakeholder "Jane, Bob, Carol"`)
  - Comma-separated names, cap at 3 (context budget)
  - Per-profile staleness checks, partial loading if some profiles missing
  - Stakeholder Advocate surfaces inter-stakeholder tensions
  - Synthesis distinguishes persona-persona vs stakeholder-stakeholder tensions
- Quality evals (v1.1, agent-as-judge)
  - 5-dimension rubric: perspective independence, domain grounding, synthesis quality, Socratic challenge, actionability
  - Weighted scoring (pass threshold: 3.5/5.0)
  - Per-test-case minimum scores calibrated to scenario strengths
- `/ds-report-gen` skill — transforms brainstorm output into dual-format reports
  - SKILL.md: 3-phase flow (input parsing → report generation → output)
  - Exec summary template (VP-ready, 400-600 words, good-vs-bad examples)
  - JSON knowledge artifact with provenance tracking (which persona, which round)
  - `--audience` flag for stakeholder-tailored framing
  - Command entry point at `.claude/commands/ds-report-gen.md`

## [1.0.0] - 2026-03-22 — MVP

### Added
- ds-brainstorm SKILL.md rewritten as fully executable Claude Code skill (135 → 680+ lines)
  - Phase 0-4 with explicit tool instructions (WebSearch, Agent, Read, Write)
  - Concrete subagent dispatch prompts with retry/error handling
  - Socratic dialogue loop with concern tracking ledger
  - Structured JSON output schema inline
- Prompt templates enhanced to copy-pasteable Agent dispatch prompts
  - build_debate_query.md: 7 variables, 7 critical rules, inline JSON schema, stakeholder integration
  - build_synthesis.md: 6-step orchestrator playbook with anti-patterns, tension formatting
- 3 eval test cases (structural, v1)
  - search-relevance-ndcg.md (easy, with --domain)
  - churn-prediction.md (medium, no domain)
  - multi-topic-scope-check.md (hard, tests scope check gate)
- Graceful degradation plan for restricted environments
  - Level 0: Full (all tools) → Level 3: Minimal (user-context only)
  - ds-brainstorm: 4-tier degradation (WebSearch → Agent → domain → user-only)
  - build-stakeholder-profile: interview-only mode when WebSearch blocked
  - Never blocks — always produces a useful brainstorm

## [0.1.0] - 2026-03-22 — Stakeholder Knowledge Layer

### Added
- `/build-stakeholder-profile` skill: interactive 6-layer stakeholder profile builder
  - SKILL.md orchestrator with 4-phase flow (intake → research → draft → enrichment → save)
  - Profile template reference (canonical 6-layer format with confidence markers)
  - Search strategy reference (web search, LinkedIn paste, public talks, Twitter, future Confluence)
  - Command entry point at `.claude/commands/build-stakeholder-profile.md`
- `stakeholders/` directory for local-only profile storage (gitignored)
- `--stakeholder` flag in ds-brainstorm SKILL.md Phase 0 (loads profile with staleness check)
- Design addendum documenting the stakeholder knowledge layer architecture

## [0.0.0] - 2026-03-22 — Scaffold

### Added
- Repo scaffolded with CLAUDE.md, skill architecture, and harness engineering design
- Design doc approved (from /office-hours brainstorming session)
- 3 persona reference files: Methodology Critic, Stakeholder Advocate, Pragmatist
- Search grounding reference with fallback protocol
- Prompt templates for debate query and synthesis
- Domain knowledge architecture with `--domain` flag
- Search relevance domain seed from Rovo Search analysis
- DS Report Generator stub (v1.1)
- Thin command entry point at `.claude/commands/ds-brainstorm.md`
