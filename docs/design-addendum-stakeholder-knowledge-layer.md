# Design Addendum: Stakeholder Knowledge Layer

**Date:** 2026-03-22
**Status:** IN PROGRESS — needs dedicated design session
**Context:** Emerged from /office-hours debate pushing deeper on why DS analyses underperform

## Core Insight

The root cause of low-impact DS analyses is NOT methodology or framing — it's **missing stakeholder context**. The brainstorm agent's value lives in the KNOWLEDGE LAYER (stakeholder profiles), not the DELIVERY MECHANISM (3-persona debate). The personas are only as good as the context they receive.

## The 6 Stakeholder Context Layers

| # | Layer | Fidelity | Confluence-Extractable? |
|---|-------|----------|------------------------|
| 1 | OKRs / stated priorities | Structured | HIGH — search OKR pages, planning docs |
| 2 | Decision patterns / past reactions | Examples | MEDIUM — comments on analysis docs, review feedback |
| 3 | Metric vocabulary | Structured | HIGH — dashboards owned, metric definitions, reports |
| 4 | Org context / political landscape | Free-text notes | LOW — tacit knowledge, user provides |
| 5 | Risk appetite / decision style | Inferred | MEDIUM — writing style analysis, uncertainty handling |
| 6 | Timing / calendar context | Free-text notes | LOW — user provides timing signals |

## Architecture Shift

```
BEFORE (current design):
  Search grounding (generic web search) → 3 personas → debate

AFTER (proposed):
  Stakeholder profiles (6 layers) + domain knowledge + search → 3 personas → debate
  │
  └── Profiles populated via Atlassian MCP (Confluence API)
      │── Search pages by author/contributor
      │── Extract OKRs, metric vocabulary, decision patterns
      │── User enriches with tacit knowledge (layers 4+6)
      └── Refresh before each brainstorm (not static)
```

## Atlassian MCP Integration

The user has Atlassian MCP available. This means:
- Confluence pages searchable by author, space, label
- Page content readable programmatically
- No API tokens or browser automation needed
- Profile generation can be automated, not manual

## Profile Generation Flow (Interactive)

1. Input: `name + level + confluence_space`
2. Agent searches Confluence via MCP for pages authored/contributed by the person
3. Agent reads top 10-15 most recent docs (OKRs, strategy, analysis reviews)
4. Agent extracts signals into 6-layer template with confidence markers
5. Agent presents draft profile to user
6. User corrects, adds tacit knowledge (layers 4+6), approves
7. Saved as `stakeholders/{name-slug}.md`
8. Before each brainstorm, agent checks if profile is stale (>2 weeks) and offers refresh

## Profile Format (Lightweight Markdown)

```markdown
# Stakeholder: {Name}
**Level:** {title}
**Last updated:** {date}
**Confidence:** {high/medium/low — based on source coverage}

## Layer 1: OKRs & Priorities (Q1 2026)
- {priority 1 — from OKR page}
- {priority 2}
- {priority 3}
**Source:** {confluence page URL}

## Layer 2: Decision Patterns
- Past win: {analysis that landed well — what made it work}
- Past miss: {analysis that didn't land — what went wrong}
- Preferred format: {1-pager vs deep dive, data-heavy vs narrative}
**Source:** {confluence comments, review feedback}

## Layer 3: Metric Vocabulary
- North star: {metric they cite in planning docs}
- Panic metric: {metric they check daily}
- Language mapping: {their term → our term, e.g., "user success" = QSR}
**Source:** {dashboards, reports they authored}

## Layer 4: Org Context [USER-PROVIDED]
- {what's competing for resources}
- {which initiatives have exec air cover}
- {what narrative they're selling upward}

## Layer 5: Risk Appetite
- Decision style: {95% confidence vs directional signal}
- Bad news handling: {shoot messenger vs reward honesty}
**Inferred from:** {writing style in docs}

## Layer 6: Timing [USER-PROVIDED]
- {board meeting in 2 weeks}
- {end of quarter — needs wins}
- {just hired new VP — landscape shifting}
```

## How Personas Use the Profile

Each persona reads the SAME profile but applies a different lens:

| Persona | How they use the profile |
|---------|------------------------|
| Methodology Critic | "Given VP tracks QSR (Layer 3), is your methodology actually measuring QSR impact? Your proposed metric (NDCG) is an offline proxy — have you validated the QSR↔NDCG correlation?" |
| Stakeholder Advocate | "VP checks DAU/MAU every morning (Layer 3 panic metric). Frame this finding as DAU/MAU movement, not NDCG improvement. Also: board meeting in 2 weeks (Layer 6) — they need ammunition, not exploration." |
| Pragmatist | "VP prefers 1-pagers (Layer 2 format preference). Your proposed 20-page deep dive won't get read. Can you distill to 1 page + appendix?" |

## Open Design Questions (for next session)

1. **Profile staleness:** How often should profiles refresh? Auto-check via MCP or user-triggered?
2. **Multi-stakeholder:** When an analysis has 3+ stakeholders, do we load all profiles? Create a composite? Ask user which is primary?
3. **Privacy:** Stakeholder profiles contain sensitive org context (Layer 4). Where should they live? Gitignored? Encrypted? Local-only?
4. **Cold start UX:** What's the minimum viable profile? Can we start with just Layer 1 (OKRs) + Layer 3 (metrics) and add layers over time?
5. **Profile as skill vs. tool:** Is the profile generator a separate skill (`/build-stakeholder-profile`) or a Phase -1 step inside ds-brainstorm?

## Next Steps

1. Start a fresh session focused on this knowledge layer design
2. Design the Atlassian MCP integration (what MCP tools to call, what to extract)
3. Build one stakeholder profile interactively as a proof of concept
4. Update the ds-brainstorm SKILL.md to consume profiles in Phase 0
5. Test: does a profile-grounded brainstorm produce meaningfully better framing than a generic one?
