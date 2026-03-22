---
name: ds-brainstorm
description: >
  Multi-persona Socratic brainstorming for DS analysis planning. Three subagents
  (Methodology Critic, Stakeholder Advocate, Pragmatist) debate your analysis plan
  with search-grounded audience intelligence. Use when planning a new DS analysis,
  exploring analytical approaches, or stress-testing an analysis plan before execution.
  Trigger: brainstorm, debate, challenge my analysis, help me think through this analysis.
---

# DS Brainstorm — Socratic Analysis Planning

## Overview

Three independent perspectives challenge your analysis plan simultaneously:
1. **Methodology Critic** — Is this analysis SOUND? (rigor, confounders, statistical methods)
2. **Stakeholder Advocate** — Will this analysis INFLUENCE decisions? (framing, metrics execs care about)
3. **Pragmatist** — Can this analysis SHIP? (data availability, timeline, feasibility)

After the three-perspective challenge, you engage in a Socratic dialogue loop where the
orchestrator pushes back on your responses until your analysis plan is sharp.

## Input

| Parameter | Required | Description |
|-----------|----------|-------------|
| Analysis question or plan | Yes | What you want to analyze, explore, or investigate |
| `--domain` | No | Domain knowledge to load (e.g., `search-relevance`, `experimentation`). Enriches all 3 personas with domain-specific vocabulary and concerns. |
| `--rounds` | No | Max Socratic dialogue rounds (default: 3) |

## Phase 0: Scope Check + Search Grounding

> Reference: `references/search-grounding.md`

1. **Scope check:** If input contains multiple distinct analysis questions, surface them
   and ask the user which to brainstorm first. One question per session.

2. **Domain loading:** If `--domain` is specified, read `references/domains/{domain}.md`
   and include it in the shared evidence block for all 3 subagents.

3. **Search grounding:** Execute ONE search step to gather:
   - Domain context (recent developments in the analysis domain)
   - Audience signals (what business leaders are discussing in this space)
   - Prior art (similar analyses done before)

4. **Evidence assembly:** Combine search results + domain knowledge + user-provided context
   into a single markdown evidence block. This block is injected verbatim into each
   subagent's dispatch prompt.

5. **Fallback:** If search returns nothing relevant, proceed with user-provided context
   and domain knowledge only. Flag to user: "Audience signals are ungrounded — brainstorm
   will rely on your context and domain knowledge."

## Phase 1: Three Perspectives (sequential in v1)

> Prompt template: `prompts/build_debate_query.md`

Dispatch each subagent sequentially (v1). Each receives:
- The user's analysis question/plan
- The shared evidence block from Phase 0
- Their persona-specific attention directive (from their reference .md file)
- Domain knowledge (if `--domain` specified)

Read each subagent's reference file for their persona definition and attention directive:
- `references/methodology-critic.md`
- `references/stakeholder-advocate.md`
- `references/pragmatist.md`

Each subagent returns a structured assessment per the observation contract in CLAUDE.md.

## Phase 2: Cross-Persona Challenge Synthesis

> Prompt template: `prompts/build_synthesis.md`

The orchestrator (this SKILL.md) reads all 3 subagent outputs and synthesizes:

1. **Agreements** — where all 3 perspectives align (strong signal)
2. **Tensions** — staged as explicit exchanges:
   "Methodology Critic says: [X]. But Pragmatist counters: [Y]."
3. **Key question for user** — the single most important tension to resolve

Present to user as a structured multi-perspective challenge, NOT consensus mush.

## Phase 3: Socratic Dialogue Loop

The orchestrator drives the loop using a unified "challenger" voice that draws on
all 3 persona outputs from Phase 1.

**Per round:**
1. User responds to the challenge synthesis
2. Orchestrator identifies which persona's concerns were addressed vs ignored
3. Orchestrator pushes back on unaddressed concerns:
   "You addressed the methodology question, but the Stakeholder Advocate's framing
   concern is still open: how would you explain this to a VP in 30 seconds?"
4. If user's response opens a fundamentally new thread, orchestrator may re-invoke
   a specific subagent for deeper follow-up

**Termination:**
- User says "enough" / "I'm good" / "let's move on"
- Max rounds reached (default 3, configurable via `--rounds`)
- Convergence: user has addressed all major tensions

**Subagent re-invocation:** Subsequent rounds do NOT re-invoke all 3 subagents.
The orchestrator uses Phase 1 outputs as reference. Only re-invoke a specific
subagent if the user fundamentally changes the analysis plan.

## Phase 4: Structured Output

Produce dual output:

1. **Human-readable summary** — narrative brainstorm recap:
   - Analysis question (restated)
   - Key decisions made during the debate
   - Open questions remaining
   - Recommended next steps

2. **Machine-readable JSON** — structured contract for downstream consumption:
   See CLAUDE.md for the full observation contract schema.
   The JSON includes perspectives, synthesis, and dialogue_history with
   `role: "user|challenger"` and `references_persona` field.

## Checklist

- [ ] Scope check passed (single analysis question)
- [ ] Domain knowledge loaded (if `--domain` specified)
- [ ] Search grounding executed (or fallback flagged)
- [ ] Evidence block assembled
- [ ] Methodology Critic dispatched and returned
- [ ] Stakeholder Advocate dispatched and returned
- [ ] Pragmatist dispatched and returned
- [ ] Synthesis produced with agreements + tensions
- [ ] Socratic dialogue loop completed (user satisfied or max rounds)
- [ ] Human-readable summary produced
- [ ] Machine-readable JSON produced
