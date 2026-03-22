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

### DS Report Generator (stub, v1.1)
- `skills/ds-report-gen/SKILL.md` — transforms brainstorm output into dual-format reports
- Consumes structured JSON from ds-brainstorm

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
  "domain_references": ["specific domain concepts referenced"]
}
```

### Error Recovery
| Error | Root Cause | Safe Retry | Stop Condition |
|-------|-----------|------------|----------------|
| Search returns nothing | Niche domain, internal-only analysis | Proceed ungrounded, flag to user | Don't retry search — proceed with user context |
| Subagent fails/times out | Context too large, model overloaded | Retry once with reduced evidence | After 1 retry, proceed with remaining personas |
| Multi-topic input | User's question is too broad | Scope-check gate: ask user to pick one | Don't attempt multi-topic brainstorm |
| Domain file not found | --domain flag with unknown domain | Proceed without domain knowledge, warn user | Don't fail — domain knowledge is optional enrichment |

### Context Budget
| Component | Budget | Notes |
|-----------|--------|-------|
| SKILL.md orchestrator | ~5% | Minimal: phase flow + dispatch logic |
| Persona reference (each) | ~5% | Loaded per subagent, not all at once |
| Domain knowledge | ~5% | Loaded only if --domain specified |
| Search evidence block | ~10% | Shared across all 3 subagents |
| Subagent responses (3x) | ~25% | Most volatile — summarize in synthesis |
| Socratic dialogue | ~40% | Grows with each round (max 3 rounds) |
| Headroom | ~10% | For reasoning during synthesis |

## Current State

v0.0 — Repo scaffolded, design doc approved. Implementation not started.
See `docs/design-20260322-ds-brainstorm-agent.md` for full design.

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
