---
name: build-stakeholder-profile
description: >
  Interactively build a 6-layer stakeholder profile for DS brainstorm grounding.
  Searches the web for public signals, presents a draft profile with confidence
  markers and gaps, then interviews the user to fill in tacit knowledge.
  Profiles are saved locally and consumed by /ds-brainstorm --stakeholder.
  Trigger: build profile, stakeholder profile, who is my audience, profile.
---

# Build Stakeholder Profile — Interactive Profile Builder

## Overview

Build a 6-layer stakeholder profile that grounds the DS Brainstorm Agent's
personas with real context about WHO will consume the analysis. The profile
captures: what the stakeholder cares about, how they make decisions, what
metrics they track, and what's happening in their world right now.

**Why this matters:** The #1 reason DS analyses don't land isn't methodology —
it's missing stakeholder context. A technically perfect analysis framed in the
wrong metrics for the wrong audience at the wrong time is wasted work.

## Input

| Parameter | Required | Description |
|-----------|----------|-------------|
| Name | Yes | Stakeholder's full name |
| `--company` | Yes | Company name (needed for search context) |
| `--role` | No | Current title/role (improves search quality) |
| `--linkedin` | No | LinkedIn profile URL (user will paste content manually) |
| `--twitter` | No | Twitter/X handle |
| `--refresh` | No | Re-run research for an existing profile, preserve user-provided layers |

## Constants

```
STALENESS_WARNING_DAYS: 14
STALENESS_CRITICAL_DAYS: 30
PROFILE_DIR: stakeholders/
MIN_VIABLE_LAYERS: [1, 3]  # OKRs + Metric Vocabulary
MAX_SEARCH_QUERIES: 4
```

## Phase 0: Intake

### If `--refresh` flag is set:

1. Look for existing profile in `stakeholders/{name-slug}.md`
2. If found: read it, note which layers are user-provided (Layers 4, 6 always;
   others if confidence = HIGH and source = user_provided)
3. Proceed to Phase 1 — web research will update external layers only
4. User-provided layers are preserved unless user explicitly wants to update them

### Standard intake (no --refresh):

1. Confirm you have the required inputs (name + company at minimum)
2. If name or company missing, ask for them conversationally:
   > "Who is the stakeholder? I need at least their name and company."
3. If optional inputs not provided, note what's missing — search will be broader

### Parse inputs and prepare:

```
stakeholder_name = {provided name}
company = {provided company}
role = {provided or "unknown"}
slug = {lowercase, hyphenated: "jane-doe"}
profile_path = stakeholders/{slug}.md
```

Check if profile already exists at `profile_path`:
- If exists and no `--refresh`: warn user and ask whether to refresh or start fresh
- If exists and `--refresh`: proceed with refresh flow (preserve user layers)
- If not exists: proceed with new profile creation

## Phase 1: Web Research

> Reference: `references/search-strategy.md`

### Graceful Degradation

If WebSearch is unavailable (blocked by corporate firewall, tool not permitted, or
errors on first attempt), skip ALL searches and go directly to **Interview-Only Mode**:

> "Web search is unavailable in this environment. I'll build this profile entirely
> from what you tell me. This works — it just means I'll ask more questions.
>
> Let's start: what does {name} care about most right now? What are their top
> 2-3 priorities this quarter?"

In interview-only mode:
- Phase 1 is replaced by a structured interview (same questions as Phase 3 enrichment, but covering ALL 6 layers instead of just gaps)
- Phase 2 still presents a draft profile, but all layers are marked `user_provided`
- The profile is still valid and usable by ds-brainstorm
- Overall confidence will be HIGH (user is authoritative) even though no external validation exists

**Detection:** Attempt the first WebSearch query. If it errors or is blocked, switch
to interview-only mode immediately. Don't retry.

### Standard Mode (WebSearch available):

Execute searches to gather raw signals. Present a brief status to the user
so they know what's happening (this takes 15-30 seconds).

> "Researching {name} at {company}... This may take a moment."

### Search execution:

Run up to 4 WebSearch queries (see search-strategy.md for exact queries):

1. **Bio + role:** `"{name}" "{company}" {role}`
2. **Public talks:** `"{name}" "{company}" presentation OR talk OR keynote`
3. **Company strategy:** `"{company}" {current_year} strategy OR priorities`
4. **Social presence:** `"{name}" site:twitter.com OR site:linkedin.com` (skip if handles provided)

### Content enrichment (optional):

If search returns URLs to talks, blog posts, or articles — fetch the top 2-3
most relevant using WebFetch. Extract signals per search-strategy.md heuristics.

### LinkedIn handling:

If `--linkedin` URL was provided OR user mentioned LinkedIn:
> "LinkedIn blocks automated access. Could you paste these sections from their profile?
> 1. **About/Summary** section
> 2. **Current role description** under Experience
> 3. **Any Featured posts or articles**
>
> Even partial info helps — paste whatever you can grab."

Wait for user response. Extract signals per search-strategy.md LinkedIn heuristics.

### Assemble raw signals:

Organize all signals by layer (see search-strategy.md "Evidence Assembly" section).
Note which layers have signals and which are empty.

## Phase 2: Draft Profile

> Reference: `references/profile-template.md`

Synthesize raw signals into a structured 6-layer profile draft. Present it
to the user with clear confidence markers and specific gap-filling questions.

### Draft assembly rules:

1. For each layer with signals: synthesize into the template format, assign
   confidence based on search-strategy.md confidence rules
2. For each layer WITHOUT signals: mark as EMPTY and prepare a specific
   question (not generic "fill this in" — ask about something concrete)
3. Layers 4 and 6 are ALWAYS marked as needing user input, even if some
   external signal exists
4. Resolve conflicts between sources: prefer more recent, prefer more specific,
   flag contradictions for user to resolve

### Presentation format:

Present the full 6-layer profile with visual markers for confidence:

```
Here's what I found for {Name}:

## Layer 1: OKRs & Priorities [MEDIUM confidence]
Based on {source description}:
- Priority 1: ...
- Priority 2: ...
- GAP: {specific question about what's missing}

## Layer 2: Decision Patterns [EMPTY]
I couldn't find public examples of how they react to analyses.
- Can you share an analysis they loved? What made it work?
- Can you share one that fell flat? What went wrong?
- Do they prefer 1-pagers or deep dives?

## Layer 3: Metric Vocabulary [MEDIUM confidence]
From their talk at {event}:
- North star: {metric}
- They referenced "{term}" 4 times — likely a key metric
- GAP: What metric do they check daily (panic metric)?

## Layer 4: Org Context [NEEDS YOUR INPUT]
This can't come from public sources. Please share:
- What's competing for their attention right now?
- Which initiatives have exec air cover?
- What narrative are they selling upward?

## Layer 5: Risk Appetite [LOW confidence]
From their communication style in {source}:
- Appears to prefer: {observation}
- GAP: Are they a "95% confidence" or "directional is fine" person?

## Layer 6: Timing [NEEDS YOUR INPUT]
- Any upcoming board meetings, QBRs, or deadlines?
- End-of-quarter pressure?
- Recent org changes?
```

## Phase 3: User Enrichment

Interactive, conversational gap-filling. NOT a form — this is a dialogue.

### Flow:

1. After presenting the draft, pause and let the user respond naturally.
   They may address multiple gaps at once or focus on one layer.

2. After each user response:
   - Update the relevant layers with what they provided
   - Set confidence to HIGH for user-provided information (source: user_provided)
   - Acknowledge what was added: "Got it — updated Layer 4 with the org context."
   - If gaps remain, ask about the next highest-priority gap

3. **Priority order for gap-filling questions:**
   - Layer 1 (OKRs) if still LOW/EMPTY — "What are their top 3 priorities this quarter?"
   - Layer 3 (Metrics) if still LOW/EMPTY — "What metrics do they track or reference in conversations?"
   - Layer 4 (Org Context) — always ask, always user-provided
   - Layer 6 (Timing) — always ask, always user-provided
   - Layer 2 (Decision Patterns) — ask if user seems knowledgeable about this person
   - Layer 5 (Risk Appetite) — ask only if other layers are well-populated

4. **Termination conditions:**
   - User says "that's all I have" / "done" / "save it" / "good enough"
   - All layers have at least LOW confidence
   - User has answered questions for Layers 4 and 6

5. **Don't over-interview.** If the user gives short answers, respect that.
   3-4 rounds of enrichment is typical. More than 5 rounds means you're
   asking too many questions — wrap up.

### Refresh mode enrichment:

When `--refresh` is active, only ask about:
- Layers that had external sources (these were re-searched — show what changed)
- Layers 4 and 6 (ask: "Has anything changed in the org context / timing since last time?")
- Do NOT re-ask about user-provided layers unless the user volunteers updates

## Phase 4: Save

### Pre-save:

1. Render the complete final profile using the exact format from
   `references/profile-template.md`
2. Calculate overall confidence:
   - HIGH: 4+ layers populated, at least 2 from external sources
   - MEDIUM: 2-3 layers populated, or mostly user-provided
   - LOW: only 1-2 layers populated
3. Set `staleness_check` to today + 30 days
4. List all sources used in the frontmatter `sources` array

### Confirm with user:

> "Here's the final profile:
>
> {rendered profile}
>
> I'll save this to: `stakeholders/{slug}.md`
> Overall confidence: {level}
> Gaps remaining: {list of EMPTY/LOW layers}
>
> Save it?"

Wait for user confirmation before writing the file.

### Save:

Write the profile to `stakeholders/{slug}.md` using the Write tool.

### Post-save:

> "Profile saved to `stakeholders/{slug}.md`
>
> To use this in a brainstorm:
>   `/ds-brainstorm --stakeholder '{name}' [your analysis question]`
>
> Profile will show a staleness warning after {STALENESS_WARNING_DAYS} days.
> Run `/build-stakeholder-profile {name} --company {company} --refresh` to update."

## Checklist

- [ ] Intake: name + company confirmed
- [ ] Existing profile check (exists? refresh? start fresh?)
- [ ] Web research executed (up to 4 queries)
- [ ] LinkedIn content requested (if URL provided)
- [ ] Raw signals assembled by layer
- [ ] Draft profile presented with confidence markers + gap questions
- [ ] User enrichment dialogue completed
- [ ] Layer 1 (OKRs) has at least LOW confidence
- [ ] Layer 3 (Metrics) has at least LOW confidence
- [ ] Layers 4 and 6 addressed (user input requested)
- [ ] Final profile rendered and confirmed with user
- [ ] Profile saved to stakeholders/{slug}.md
- [ ] Usage instructions shown to user
