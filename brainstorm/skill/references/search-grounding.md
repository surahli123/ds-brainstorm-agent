# Search Grounding — Phase 0 Evidence Assembly

## Purpose

Execute ONE search step before subagent dispatch to ground the brainstorm in real-world context. All 3 personas receive the same evidence block with different attention directives.

## Search Strategy

Gather 3 types of signals:

### 1. Domain Context
- Web search for recent developments in the user's analysis domain
- Query: "[analysis topic] [domain] recent developments"
- Goal: what's the current state of knowledge?

### 2. Audience Signals
- Web search for what business leaders discuss in this space
- Query: "[industry/domain] executive priorities [current year]"
- Goal: what do stakeholders actually care about?
- Note: v1 signals are generic industry-level, not company-specific

### 3. Prior Art
- Web search for similar analyses
- Query: "[analysis approach] [domain] case study OR analysis"
- Goal: has someone done this before? What worked?

## Evidence Block Assembly

Combine all search results into a single markdown section:

```markdown
## Shared Evidence Block

### Domain Context
[search results — 3-5 most relevant findings]

### Audience Signals
[search results — 3-5 most relevant business context signals]

### Prior Art
[search results — 2-3 most relevant similar analyses]

### Domain Knowledge (loaded via --domain)
[contents of references/domains/{domain}.md, if specified]

### User-Provided Context
[any additional context from the user's input or project CLAUDE.md]
```

## Confluence Search (when Atlassian MCP available)

### Priority: ABOVE web search

Internal documentation is more authoritative than public web results for questions
about your own systems. When Confluence is available, it is the primary search channel.

### Search query construction

- Use the analysis topic as the primary search term
- Add qualifying terms: "metric definition", "architecture", "RFC", "decision"
- Do NOT use generic terms like "best practices" — Confluence search is for YOUR
  system's specifics, not general knowledge

### Result handling

- Extract: title, space, last_updated, relevant excerpt
- Flag stale docs (>6 months old): note "may be outdated — verify with team"
- If Confluence returns relevant results, REDUCE web search to 1 query
  (external context only — skip audience signals and prior art)

### When Confluence is NOT available

Skip silently. Do not warn the user — they know their environment. Fall back to
web search + domain knowledge + external knowledge directory as usual.

## Fallback Protocol

If search returns nothing relevant:
1. Proceed with domain knowledge + user-provided context only
2. Flag to user: "Audience signals are ungrounded — brainstorm will rely on your context and domain knowledge."
3. Stakeholder Advocate should note this limitation in their assessment
4. Do NOT retry search or block on search failure

## Error Recovery

| Error | Response |
|-------|----------|
| Search API timeout | Proceed ungrounded, flag to user |
| All results irrelevant | Proceed ungrounded, flag to user |
| Domain file not found | Warn user, proceed without domain enrichment |
| Partial results (1 of 3 searches fails) | Use what you have, note gap |
