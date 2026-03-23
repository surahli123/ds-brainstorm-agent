# DS Brainstorm Agent

## What This Is

A multi-persona Socratic brainstorming agent for data science analysis planning. Three subagents (Methodology Critic, Stakeholder Advocate, Pragmatist) debate your analysis plan with search-grounded audience intelligence, then engage you in a Socratic dialogue to sharpen your approach.

**Architecture:** Hybrid ReAct (orchestrator planning) + structured tool execution (subagent dispatch).

## Skill Architecture

### DS Brainstorm
- `skills/ds-brainstorm/SKILL.md` — orchestrator (Phases 0-4: scope check → search → dispatch → synthesis → Socratic loop)
- `skills/ds-brainstorm/references/methodology-critic.md` — subagent: challenges analytical rigor
- `skills/ds-brainstorm/references/stakeholder-advocate.md` — subagent: frames for business impact
- `skills/ds-brainstorm/references/pragmatist.md` — subagent: checks feasibility and data availability
- `skills/ds-brainstorm/references/domains/` — domain knowledge files loaded via `--domain` flag
- `skills/ds-brainstorm/references/search-grounding.md` — Phase 0 search strategy + evidence assembly
- `skills/ds-brainstorm/prompts/build_debate_query.md` — per-persona dispatch prompt template
- `skills/ds-brainstorm/prompts/build_synthesis.md` — cross-persona synthesis template

### Build Stakeholder Profile
- `skills/build-stakeholder-profile/SKILL.md` — interactive 6-layer profile builder
- `skills/build-stakeholder-profile/references/profile-template.md` — canonical profile format (the contract)
- `skills/build-stakeholder-profile/references/search-strategy.md` — source-specific extraction guidance
- Profiles saved to `stakeholders/{slug}.md` (gitignored, local-only)
- Consumed by ds-brainstorm via `--stakeholder` flag in Phase 0

### DS Report Generator
- `skills/ds-report-gen/SKILL.md` — transforms brainstorm JSON into dual-format reports
- `skills/ds-report-gen/references/report-template.md` — exec summary + JSON artifact templates
- `skills/ds-report-gen/prompts/build_report.md` — report assembly prompt with extraction logic
- Consumes structured JSON from ds-brainstorm Phase 4
- `--audience` flag loads stakeholder profile for tailored framing

### Evals
- `skills/ds-brainstorm/evals/evals.json` — 3 test cases (structural + quality)
- `skills/ds-brainstorm/evals/quality-rubric.md` — 5-dimension agent-as-judge rubric
- `skills/ds-brainstorm/evals/test-cases/` — detailed test case descriptions

## Agent Harness Design

### Action Space (3 medium-granularity subagents + 1 search tool)
| Tool | Risk | Granularity | Input | Output |
|------|------|-------------|-------|--------|
| methodology-critic | Low | Medium | analysis plan + evidence block + domain knowledge | structured assessment (status, challenges, recommendations) |
| stakeholder-advocate | Low | Medium | analysis plan + evidence block + domain knowledge | structured framing (narrative hook, key metrics, decision enablement) |
| pragmatist | Low | Medium | analysis plan + evidence block + domain knowledge | structured feasibility (data availability, effort, scope recommendation) |
| search-grounding | Medium | Medium | analysis question + domain context | evidence block (domain signals, audience signals, prior art) |

### Observation Contract
Every subagent returns:
```json
{
  "status": "success|warning|error",
  "summary": "one-line assessment",
  "perspective": "methodology_critic|stakeholder_advocate|pragmatist",
  "assessment": "SOUND|CONCERNS|MAJOR_ISSUES",
  "findings": [...],
  "next_actions": ["what the user should address"],
  "domain_references": ["specific domain concepts referenced"],
  "stakeholder_tensions": ["optional — present only in multi-stakeholder mode"]
}
```

### Error Recovery
| Error | Root Cause | Safe Retry | Stop Condition |
|-------|-----------|------------|----------------|
| Search returns nothing | Niche domain, internal-only analysis | Proceed ungrounded, flag to user | Don't retry search — proceed with user context |
| Subagent fails/times out | Context too large, model overloaded | Retry once with reduced evidence | After 1 retry, proceed with remaining personas |
| Multi-topic input | User's question is too broad | Scope-check gate: ask user to pick one | Don't attempt multi-topic brainstorm |
| Domain file not found | --domain flag with unknown domain | Proceed without domain knowledge, warn user | Don't fail — domain knowledge is optional enrichment |
| WebSearch blocked | Corporate firewall, tool not permitted | Don't retry — switch to ungrounded mode | Proceed with domain + stakeholder + user context only |
| Agent tool blocked | Environment restricts subagent dispatch | Run single-agent inline mode (all 3 perspectives in one context) | Quality drops but still functional |
| All tools blocked | Maximally restricted environment | Interview-only mode (profile builder), user-context-only mode (brainstorm) | Still valuable — structured multi-perspective review with general knowledge |

### Graceful Degradation Levels (ds-brainstorm)
| Level | What's Blocked | Capability | Quality |
|-------|---------------|------------|---------|
| 0: Full | Nothing | Full search grounding + parallel subagents | Best |
| 1: No WebSearch | Web access blocked | Domain knowledge + stakeholder + user context | Good |
| 2: No WebSearch + No Agent | Web + subagent dispatch blocked | Single-agent inline brainstorm | Moderate |
| 3: Minimal | All external enrichment blocked | User-context-only brainstorm | Baseline |

### Context Budget
| Component | Budget | Notes |
|-----------|--------|-------|
| SKILL.md orchestrator | ~15% | Expanded: phase flow + inline dispatch prompts + degradation logic |
| Persona reference (each) | ~3% | Loaded per subagent, not all at once |
| Domain knowledge | ~5% | Loaded only if --domain specified |
| Stakeholder profile (each) | ~3% | Loaded only if --stakeholder specified, cap 3 (~9% max) |
| Search evidence block | ~10% | Shared across all 3 subagents |
| Subagent responses (3x) | ~20% | Most volatile — summarize in synthesis |
| Socratic dialogue | ~30% | Grows with each round (max 3 rounds, 2 if 3 stakeholders) |
| Headroom | ~10% | For reasoning during synthesis |

## Current State

v1.1 — Full feature set implemented.
- ds-brainstorm: parallel subagent dispatch (with sequential + inline fallback), multi-stakeholder support (up to 3), Socratic loop, structured output
- build-stakeholder-profile: interactive 6-layer profile builder (smoke-tested with Peter Yang), interview-only degradation mode
- ds-report-gen: dual-format reports (exec summary + JSON artifact), audience-tailored framing
- Evals: 3 test cases with structural checks + 5-dimension quality rubric (agent-as-judge)
- Graceful degradation at every level (parallel → sequential → inline → user-only)
See `docs/design-20260322-ds-brainstorm-agent.md` for base design.
See `docs/design-addendum-stakeholder-knowledge-layer.md` for knowledge layer design.

## Domain Context: ACTIVE

Search relevance and DS expertise applies. Domain knowledge for search-relevance seeded from Rovo Search analysis (`skills/ds-brainstorm/references/domains/search-relevance.md`).

## Pickup Instructions

Every session start:
1. Read this CLAUDE.md
2. Read `docs/design-20260322-ds-brainstorm-agent.md` for the approved design
3. Check `dev/sessions/` for latest session context
4. Check `dev/decisions/` before making architectural choices

## Session End Protocol

Before ending every session:
1. Create `dev/sessions/YYYY-MM-DD-description.md`
2. Update CHANGELOG.md if anything shipped
3. Create `dev/decisions/ADR-NNN.md` if a design choice was made
