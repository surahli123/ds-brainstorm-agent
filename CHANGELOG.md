# Changelog

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
