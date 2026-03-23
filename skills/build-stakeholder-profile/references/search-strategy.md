# Search Strategy: Stakeholder Profile Building

## Purpose

Defines how to gather signals about a stakeholder from external sources and map
them to the 6-layer profile template. Each source has specific search queries,
extraction heuristics, and confidence assignment rules.

The profile schema is SOURCE-AGNOSTIC. This file defines source-specific
strategies. Adding a new source (e.g., Confluence MCP) means adding a new
section here — no schema changes needed.

## Source: Web Search

**Tool:** WebSearch
**Layers fed:** 1 (OKRs), 3 (Metrics), 5 (Risk Appetite)
**Default confidence:** MEDIUM (public info, may be outdated)

### Queries to Execute (in order)

1. **Bio + role context:**
   `"{name}" "{company}" {role}`
   - Extract: current responsibilities, team scope, recent initiatives
   - Feeds: Layer 1 (priorities from role description)

2. **Public talks + thought leadership:**
   `"{name}" "{company}" presentation OR talk OR keynote OR conference`
   - Extract: topics they present on (= what they care about publicly),
     metrics they reference, frameworks they use
   - Feeds: Layer 1 (stated priorities), Layer 3 (metric vocabulary),
     Layer 5 (communication style as proxy for decision style)

3. **Company strategy context:**
   `"{company}" {current_year} priorities OR strategy OR OKRs OR annual report`
   - Extract: company-level priorities that flow down to this stakeholder
   - Feeds: Layer 1 (priorities inherited from company strategy)

4. **Social presence (optional, if no handle provided):**
   `"{name}" site:twitter.com OR site:linkedin.com OR site:medium.com`
   - Extract: topics they post about, metrics they reference publicly
   - Feeds: Layer 3 (metric vocabulary), Layer 5 (communication patterns)

### Extraction Heuristics

When reading search results, look for:

- **Priority signals:** Words like "focus on", "our top priority", "we're investing in",
  "critical initiative", "key metric". These map to Layer 1.
- **Metric signals:** Specific numbers, KPI names, dashboard references, "we track",
  "we measure success by". These map to Layer 3.
- **Style signals:** How they communicate uncertainty ("we believe" vs "the data shows"),
  how they handle questions ("great question" vs redirects). These map to Layer 5.
- **Recency:** Prioritize content from the last 6 months. Older content may reflect
  outdated priorities. Note the date of each source.

### Confidence Assignment

| Signal strength | Confidence | Example |
|----------------|------------|---------|
| Direct quote with specific metrics | MEDIUM-HIGH | "Our north star is DAU/MAU" in a keynote |
| Mentioned in company report/press | MEDIUM | Company annual report cites "search quality" as priority |
| Inferred from role/team scope | LOW | VP of Search probably cares about search metrics |
| No signal found | EMPTY | Web search returned nothing relevant |

Note: Web search alone never reaches HIGH confidence. HIGH requires user confirmation.

## Source: User-Pasted LinkedIn Content

**Tool:** User provides via conversation (LinkedIn blocks scraping)
**Layers fed:** 1 (OKRs), 2 (Decision Patterns), 3 (Metrics)
**Default confidence:** HIGH (user verified the content)

### What to Request

If the user has a LinkedIn URL or mentions LinkedIn:

> "LinkedIn blocks automated access. Could you paste these sections from their profile?
> 1. **About/Summary** section (helps with priorities and metric vocabulary)
> 2. **Current role description** under Experience (helps with scope and focus areas)
> 3. **Any Featured posts or articles** (helps with thought leadership topics)
>
> Even partial info helps — paste whatever you can grab."

### Extraction Heuristics

- **About section:** Usually contains stated priorities, areas of expertise,
  and sometimes specific metrics. Map to Layer 1 + Layer 3.
- **Role description:** Scope of responsibility, team size, key initiatives.
  Map to Layer 1.
- **Featured content:** Topics they promote publicly = what they want to be
  known for. Cross-reference with Layer 1 priorities.
- **Recommendations received:** (if pasted) Reveal how others perceive their
  decision style. Map to Layer 2 + Layer 5.

## Source: Public Talks / Blog Posts

**Tool:** WebFetch (to read content from URLs found via WebSearch)
**Layers fed:** 1 (OKRs), 3 (Metrics), 5 (Risk Appetite)
**Default confidence:** MEDIUM

### When to Use

When web search returns URLs to talks, blog posts, or articles authored by or
featuring the stakeholder. Fetch the top 2-3 most recent and relevant.

### Extraction Heuristics

- **Slide decks / talk summaries:** Look for "key takeaways", "what we learned",
  metrics cited, before/after comparisons. These reveal what they consider
  important enough to present publicly.
- **Blog posts:** Topic = priority. Metrics cited = vocabulary. Tone = style.
  Look for recurring themes across multiple posts.
- **Interview quotes:** Direct quotes are gold — they reveal how the person
  frames problems and what language they use naturally.

## Source: Twitter/X

**Tool:** WebSearch with `site:twitter.com` or `site:x.com`
**Layers fed:** 3 (Metrics), 5 (Risk Appetite)
**Default confidence:** LOW-MEDIUM (tweets are informal, may not reflect work priorities)

### Queries

If Twitter/X handle is known:
`from:{handle} data OR metrics OR launch OR shipped`

If handle unknown:
`"{name}" site:twitter.com OR site:x.com`

### Extraction Heuristics

- **What they retweet/share:** Topics they amplify = what they value
- **How they discuss results:** "Shipped!" vs "Cautiously optimistic about early results"
  reveals risk appetite (Layer 5)
- **Metric mentions:** Any specific KPIs they cite publicly

### Caveat

Many executives have limited or no Twitter presence. If search returns nothing,
skip this source entirely — don't waste time.

## Source: Confluence (via Atlassian MCP) [FUTURE]

**Tool:** Atlassian MCP tools (confluence_search, confluence_get_page)
**Layers fed:** 1, 2, 3, 5 (potentially all non-user layers)
**Default confidence:** HIGH (internal docs are authoritative)
**Status:** Not available locally. Available in internal environment.

### Planned Queries (for when MCP is configured)

1. `contributor:{name} space:{space} type:page` — pages they authored
2. `label:okr contributor:{name}` — their OKR pages
3. `label:review label:analysis contributor:{name}` — their analysis reviews
4. Search for dashboard links in pages they authored (Layer 3)
5. Read comments they left on analysis docs (Layer 2 — decision patterns)

### Why Confluence is the Best Source

Internal documents are the most authoritative source for Layers 1-3 and
partially Layer 5. A stakeholder's Confluence pages contain:
- Their actual OKRs (not public-facing versions)
- Real metric definitions from dashboards they own
- Review comments that reveal decision patterns
- Writing style that reveals risk appetite

When Confluence MCP becomes available, it should be the PRIMARY source,
with web search as supplementary context.

## Evidence Assembly

After gathering signals from all available sources, assemble them into
a single evidence block organized by layer. Each signal includes:

```markdown
### Raw Signals for {Name}

#### Layer 1 Signals (OKRs & Priorities)
- [SOURCE: web_search, DATE: 2026-03] {signal text}
- [SOURCE: linkedin_paste, DATE: current] {signal text}

#### Layer 3 Signals (Metric Vocabulary)
- [SOURCE: public_talk, DATE: 2026-01, URL: ...] {signal text}

#### Layer 5 Signals (Risk Appetite)
- [SOURCE: twitter, DATE: 2026-02] {signal text}

#### No Signals Found For:
- Layer 2 (Decision Patterns) — user must provide
- Layer 4 (Org Context) — always user-provided
- Layer 6 (Timing) — always user-provided
```

This evidence block feeds into the draft profile assembly step.
The agent synthesizes signals into structured profile layers, resolving
conflicts (newer source wins) and flagging contradictions.
