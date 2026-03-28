# Changelog

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
