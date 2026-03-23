# Stakeholder Profile Template

## Purpose

This is the canonical format for stakeholder profiles. Every profile produced by
`/build-stakeholder-profile` MUST follow this format exactly. Consuming skills
(ds-brainstorm, ds-report-gen) depend on this structure.

## YAML Frontmatter Schema

```yaml
---
name: {Full Name}
role: {Current Title}
company: {Company Name}
created: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
confidence: {overall — high | medium | low}
sources:
  - {source_type}  # web_search, user_provided, public_talk, linkedin_paste, twitter, confluence
staleness_check: {YYYY-MM-DD — updated + 30 days}
---
```

**Confidence rules:**
- `high` — 4+ layers populated, at least 2 from external sources
- `medium` — 2-3 layers populated, or mostly user-provided
- `low` — only 1-2 layers populated, minimal external validation

## Profile Body (6 Layers)

### Layer 1: OKRs & Priorities

What this stakeholder cares about RIGHT NOW. Quarterly goals, stated priorities,
strategic focus areas. This is the most important layer — without it, the
brainstorm agent can't frame recommendations in terms the stakeholder values.

```markdown
## Layer 1: OKRs & Priorities
**Confidence:** {HIGH | MEDIUM | LOW | EMPTY}
**Quarter:** {Q? YYYY}

- {Priority 1 — specific, not vague. "Reduce query abandonment by 15%" not "improve search"}
- {Priority 2}
- {Priority 3}

**Source:** {where this came from — URL, "user-provided", "inferred from [doc]"}
```

### Layer 2: Decision Patterns

How this stakeholder reacts to analyses. What formats work, what makes them
say yes, what makes them tune out. This layer is the hardest to populate from
public sources — it usually comes from the user's direct experience.

```markdown
## Layer 2: Decision Patterns
**Confidence:** {HIGH | MEDIUM | LOW | EMPTY}

- **Past win:** {an analysis that landed well — what made it work}
- **Past miss:** {an analysis that didn't land — what went wrong}
- **Preferred format:** {1-pager vs deep dive, data-heavy vs narrative, async vs live}
- **Decision trigger:** {what makes them act — urgency, data threshold, peer pressure}

**Source:** {where this came from}
```

### Layer 3: Metric Vocabulary

The metrics this stakeholder uses when they talk about success. Critical for
framing — if you use "NDCG" and they think in "query success rate", your
analysis won't land even if the content is perfect.

```markdown
## Layer 3: Metric Vocabulary
**Confidence:** {HIGH | MEDIUM | LOW | EMPTY}

- **North star:** {the metric they cite in planning docs and all-hands}
- **Panic metric:** {the metric they check daily — what keeps them up at night}
- **Language mapping:** {their term -> our term, e.g., "user success" = QSR, "findability" = Recall@10}
- **Metrics they ignore:** {metrics that are important to DS but this stakeholder doesn't track}

**Source:** {where this came from — dashboards, reports, public talks}
```

### Layer 4: Org Context [USER-PROVIDED]

Political landscape, resource competition, internal narratives. This layer
CANNOT be populated from external sources — it always comes from the user.

```markdown
## Layer 4: Org Context
**Confidence:** {HIGH | MEDIUM | LOW | EMPTY}
**Note:** User-provided — not extractable from public sources

- {What's competing for their attention/resources right now}
- {Which initiatives have executive air cover}
- {What narrative they're selling upward to their leadership}
- {Recent org changes — new hires, departures, reorgs}

**Source:** user-provided
```

### Layer 5: Risk Appetite

How this stakeholder handles uncertainty, bad news, and ambiguity. Inferred
from writing style and public behavior — low confidence unless user confirms.

```markdown
## Layer 5: Risk Appetite
**Confidence:** {HIGH | MEDIUM | LOW | EMPTY}

- **Decision style:** {needs 95% confidence vs acts on directional signal}
- **Bad news handling:** {shoots the messenger vs rewards honesty vs ignores inconvenient data}
- **Ambiguity tolerance:** {comfortable with "we don't know yet" vs demands answers now}

**Inferred from:** {writing style in docs, public talks, user knowledge}
```

### Layer 6: Timing [USER-PROVIDED]

Calendar context that affects how to frame and time the analysis delivery.
Always user-provided — this changes frequently.

```markdown
## Layer 6: Timing
**Confidence:** {HIGH | MEDIUM | LOW | EMPTY}
**Note:** User-provided — changes frequently, check before each brainstorm

- {Upcoming deadlines — board meetings, QBRs, planning cycles}
- {End-of-quarter pressure — needs wins vs has runway}
- {Landscape shifts — new VP hired, reorg announced, strategy pivot}

**Source:** user-provided
```

## Cold Start Minimum

A profile is USABLE (can be loaded into ds-brainstorm) when:
- Layer 1 (OKRs) has at least LOW confidence, AND
- Layer 3 (Metric Vocabulary) has at least LOW confidence

A profile is EMPTY and should NOT be loaded when both Layer 1 and Layer 3 are EMPTY.
In that case, ask the user directly: "What are their top 3 priorities?" and
"What metrics do they track or reference?"

## Staleness Thresholds

| Age | Status | Behavior |
|-----|--------|----------|
| < 14 days | Fresh | Load silently |
| 14-30 days | Aging | Load with warning: "Profile last updated N days ago" |
| > 30 days | Stale | Warn: "Profile is N days old. OKRs and timing likely outdated. Consider refreshing." |

Never block on staleness — stale context beats no context.
