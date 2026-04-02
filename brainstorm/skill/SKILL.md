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
| `--knowledge-dir` | No | Path to external domain knowledge directory (e.g., `~/projects/Search_Metric_Analyzer/domains/search_metrics/knowledge/`). Loads YAML/md summaries into evidence block. |
| `--stakeholder` | No | Stakeholder name(s) to load profiles for. Supports comma-separated names for multi-stakeholder mode (e.g., `--stakeholder "Jane Doe, Bob Smith"`). Cap: 3 stakeholders max. Loads from `stakeholders/{slug}.md`. Enriches all 3 personas with stakeholder-specific context. Build profiles first with `/build-stakeholder-profile`. |
| `--rounds` | No | Max Socratic dialogue rounds (default: 3) |

---

## Phase 0: Scope Check + Search Grounding

**Goal:** Validate the user has a single, brainstormable question, then gather real-world
evidence to ground the debate. This phase produces the **evidence block** — a markdown
string that all 3 subagents receive identically.

### Step 0.1: Scope Check

Read the user's input. If it contains **multiple distinct analysis questions**, list them
and ask the user which ONE to brainstorm first. Do not proceed until you have a single question.

**How to detect multi-topic input:**
- Multiple question marks addressing different subjects
- "Also, I want to analyze..." or "Another thing..."
- Distinct analytical goals that would need separate methodologies

If ambiguous, ask: *"I see a few threads here. Which one should we dig into first?"*

### Step 0.2: Domain Knowledge Loading

If `--domain` is specified, use `Read` to load the domain file:

```
Read file: skills/ds-brainstorm/references/domains/{domain}.md
```

- **If the file exists:** Store its contents as `domain_knowledge` for inclusion in the evidence block.
- **If the file does not exist:** Warn the user: *"No domain knowledge file found for '{domain}'. Proceeding without domain enrichment. Available domains are in `skills/ds-brainstorm/references/domains/`."* Set `domain_knowledge` to empty string.

### Step 0.2b: External Knowledge Directory (if --knowledge-dir specified)

If `--knowledge-dir` is provided:

1. **Verify directory exists** using `Glob` on `{knowledge-dir}/*.yaml` and `{knowledge-dir}/*.md`.
   If no files found, warn: *"No knowledge files found at '{knowledge-dir}'. Proceeding without external knowledge."*

2. **Build knowledge summary.** For each `.yaml` file found:
   - Read the file
   - Extract top-level keys and their `description` or `function` fields (first level only)
   - Do NOT load full file contents — they're too large for context budget

3. **Store as `external_knowledge_summary`** — a markdown summary like:
   ```
   **metric_definitions.yaml:** click_quality, search_quality_success, ai_trigger_rate, ...
   **search_pipeline_knowledge.yaml:** query_understanding, content_classification, ranking, neural_retrieval, ...
   **architecture_tradeoffs.yaml:** model_tiering, batch_processing, feature_caching, ...
   ```

4. **For each `.md` file found:** Read the first 10 lines as a summary. Include filename
   and the first non-empty line as a one-line description.

5. **On-demand deep reads (Phase 3 only).** During Phase 3 Socratic dialogue, if a specific
   component comes up that the knowledge summary doesn't cover in depth, read the relevant
   YAML section using `Grep` or `Read` with offset, and incorporate it into the orchestrator's
   follow-up challenge. During initial Phase 1 dispatch, the summary-level knowledge is sufficient.

### Step 0.3: Stakeholder Profile Loading

If `--stakeholder` is specified:

1. **Parse names:** Split the `--stakeholder` value by commas, trim whitespace from each name.
   Example: `"Jane Doe, Bob Smith"` → `["Jane Doe", "Bob Smith"]`

2. **Enforce cap:** If more than 3 names are provided, warn:
   *"Multi-stakeholder mode supports up to 3 stakeholders. You provided {N}. Which 3 should I prioritize?"*
   Wait for the user to pick before proceeding. Do not silently truncate.

3. **For EACH name in the list:**

   a. **Convert name to slug:** lowercase, replace spaces with hyphens.
      Example: "Jane Doe" → "jane-doe"

   b. **Read the profile** using `Read`:
      ```
      Read file: stakeholders/{slug}.md
      ```

   c. **If the file exists**, check the `updated` date in the YAML frontmatter:
      - **Fresh (<14 days old):** Load silently.
      - **Aging (14-30 days old):** Load it, but warn:
        *"Stakeholder profile for '{name}' last updated N days ago. Priorities may have shifted."*
      - **Stale (>30 days old):** Load it, but warn:
        *"Stakeholder profile for '{name}' is N days old. Consider running `/build-stakeholder-profile {name} --refresh`."*
      Stale context beats no context — always load it.

   d. **If the file does not exist:** Warn:
      *"No profile found for '{name}'. Run `/build-stakeholder-profile {name} --company [company]` to create one."*
      Skip this name and continue loading the rest.

4. **Collect results:** Store all successfully loaded profiles in `stakeholder_profiles` (a list).
   If some profiles loaded and some did not, proceed with what exists and note the missing ones:
   *"Loaded profiles for: {loaded names}. Missing profiles for: {missing names}. Proceeding with available context."*

5. **Include ALL loaded profiles in the evidence block**, each as a separate section:
   ```
   ### Stakeholder Profile: Jane Doe
   [profile contents]

   ### Stakeholder Profile: Bob Smith
   [profile contents]
   ```

6. **Context budget note:** Each additional stakeholder profile costs ~3% of context budget.
   With 3 profiles loaded, total stakeholder context is ~9%. This reduces headroom for the
   Socratic dialogue — consider keeping dialogue to 2 rounds when 3 stakeholders are loaded.

### Step 0.3b: Confluence Search (if Atlassian MCP available)

**Detection:** Check if `mcp__atlassian__search_confluence` tool is available.
If not available: skip silently. Log internally: "Confluence MCP not available — using web search only."

If available, run 3 targeted Confluence searches BEFORE web search (internal docs are
authoritative for questions about your own systems):

1. **Metric definitions:**
   Query: `{analysis_topic} AND (metric definition OR measurement)`
   Goal: Find how this metric is actually computed internally

2. **System architecture:**
   Query: `{analysis_topic} AND (architecture OR design doc OR RFC)`
   Goal: Find system design docs for the components being analyzed

3. **Decision history:**
   Query: `{analysis_topic} AND (decision OR tradeoff OR retrospective)`
   Goal: Find what was already considered and rejected

Note: If the Atlassian MCP uses CQL, use CQL syntax. Otherwise use natural language
queries without exact-match quoting — quoted strings produce exact phrase matches
which are too restrictive.

Store results as `confluence_results`. These go ABOVE web search results in the
evidence block (internal docs take priority).

If Confluence returns results, REDUCE web search to 1 query (external context only —
skip audience signals and prior art searches, which are less useful when internal
docs are available).

### Step 0.4: Search Grounding

Execute **three `WebSearch` calls** to gather real-world evidence. These can run in parallel
since they are independent.

> **Why search?** Without grounding, the subagents can only challenge based on general
> knowledge. Search evidence gives them specific, current context — what's trending in
> the domain, what execs actually care about, what similar analyses have looked like.

**Search 1 — Domain Context** (what's the current state of knowledge?):
```
WebSearch query: "{analysis_topic} {domain} recent developments {current_year}"
```

**Search 2 — Audience Signals** (what do business leaders care about?):
```
WebSearch query: "{industry_or_domain} executive priorities data analytics {current_year}"
```

**Search 3 — Prior Art** (has someone done this before?):
```
WebSearch query: "{analysis_approach} {domain} case study OR analysis"
```

Replace `{analysis_topic}`, `{domain}`, `{industry_or_domain}`, and `{analysis_approach}`
with specifics extracted from the user's input. Use your judgment to craft queries that
will return useful results — the templates above are starting points, not rigid formulas.

### Step 0.5: Evidence Block Assembly

Combine all gathered context into a single markdown string called `evidence_block`.
This exact string gets injected into every subagent's prompt.

Assemble it in this structure:

```markdown
## Shared Evidence Block

### Confluence Context (internal docs — highest authority)
[Results from Step 0.3b Confluence search, if available.]
[If Confluence MCP not available: omit this section entirely.]

### External Domain Knowledge (loaded via --knowledge-dir)
[Summary from Step 0.2b, if --knowledge-dir specified.]
[If not specified: omit this section entirely.]

### Domain Knowledge (loaded via --domain)
[Contents of domain_knowledge, or "No domain knowledge loaded." if --domain not specified]

### Domain Context (web search)
[3-5 most relevant findings from Search 1. Include source URLs.]
[If Search 1 returned nothing: "No domain context found via search."]

### Audience Signals (web search)
[3-5 most relevant business context signals from Search 2. Include source URLs.]
[If Search 2 returned nothing: "No audience signals found via search."]

### Prior Art (web search)
[2-3 most relevant similar analyses from Search 3. Include source URLs.]
[If Search 3 returned nothing: "No prior art found via search."]

### Stakeholder Profiles
[For EACH loaded profile, include a subsection:]

#### Stakeholder Profile: {name_1}
[Contents of first stakeholder_profile]

#### Stakeholder Profile: {name_2}
[Contents of second stakeholder_profile, if applicable]

[Omit this section entirely if --stakeholder not specified.
 If only one stakeholder loaded, include just that one subsection.]

### User-Provided Context
[The user's original analysis question/plan, verbatim]
```

### Step 0.6: Fallback Handling

If ALL three searches return nothing relevant:
1. Proceed with domain knowledge + stakeholder profile + user context only.
2. Tell the user: *"Search grounding returned no relevant results — the brainstorm will
   rely on your context and domain knowledge. Audience signals are ungrounded."*
3. Still assemble the evidence block with whatever you have.
4. **Do NOT retry search or block on search failure.** The brainstorm is still valuable
   without search — it just lacks external grounding.

If **some** searches succeed and others fail, use what you have and note the gap in
the evidence block (e.g., "No prior art found via search.").

### Graceful Degradation Plan

The brainstorm agent must work even when the environment restricts tool access.
Degradation is tiered — the agent drops capabilities gracefully, never blocks.

| Degradation Level | What's Blocked | Impact | Mitigation |
|-------------------|---------------|--------|------------|
| **Level 0: Full** | Nothing | Full grounding | N/A — happy path |
| **Level 1: No WebSearch** | WebSearch tool unavailable or blocked by firewall/policy | No external grounding (domain context, audience signals, prior art) | Skip Step 0.4 entirely. Evidence block contains only: domain knowledge (if `--domain`), stakeholder profile (if `--stakeholder`), user-provided context. Tell user: *"Web search is unavailable in this environment. Brainstorm will rely on domain knowledge, stakeholder profile, and your context. Consider providing extra context about recent developments in your domain."* |
| **Level 2: No WebSearch + No Agent** | WebSearch AND Agent tool unavailable | No subagent dispatch — can't run 3 independent perspectives | Run the orchestrator as a **single-agent brainstorm**: read all 3 persona files, adopt each perspective sequentially in the SAME context, produce all 3 assessments inline. Quality drops (perspectives may anchor on each other) but still functional. Tell user: *"Running in single-agent mode — perspectives may be less independent than usual."* |
| **Level 3: No WebSearch + No Agent + No Domain** | All external enrichment blocked AND no `--domain` file found | Only user context available | Still run the brainstorm using ONLY the user's input. The 3 perspectives challenge based on general DS knowledge. Tell user: *"Running with minimal context. The more detail you provide about your analysis plan, data, and stakeholders, the sharper the debate will be."* |

**Detection:** At the START of Phase 0, attempt each tool in order:
1. Try `Read` on a domain file (if `--domain` specified) — if blocked, note Level 3
2. Try `WebSearch` with a simple test query — if blocked/errors, note Level 1
3. Phases 1-3 will detect Agent tool availability when first dispatch is attempted

**Critical rule:** NEVER fail the brainstorm because a tool is unavailable. The debate
is valuable at every degradation level — it just gets sharper with more context.
At Level 3 (user context only), the brainstorm is equivalent to a well-structured
multi-perspective review. That's still better than no review at all.

---

## Phase 1: Three Perspectives (Parallel Subagent Dispatch)

**Goal:** Get three independent, structured assessments of the user's analysis plan.
Each subagent runs in isolation so their perspectives don't anchor on each other.

> **Why parallel?** All 3 subagents are independent — they receive the same evidence block
> and don't read each other's output. Dispatching them in a single message lets the
> environment run them concurrently, cutting wall-clock time from ~3x to ~1x. If the
> environment doesn't support concurrent Agent calls, we fall back to sequential dispatch
> with the exact same prompts.

### Dispatch Mode

The orchestrator attempts parallel dispatch by default and degrades automatically.

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Parallel (default)** | Agent tool supports multiple concurrent calls | Dispatch all 3 Agent calls in a single message. Wait for all to return. |
| **Sequential (fallback)** | First parallel dispatch fails with a tool-availability or concurrency error (not a content error) | Dispatch one at a time: Critic → Advocate → Pragmatist. Same prompts, just serialized. |
| **Single-agent inline (Level 2)** | Agent tool unavailable entirely | Already handled in the Graceful Degradation Plan (Phase 0). Do not duplicate — follow Level 2 instructions there. |

**Detection logic:**

1. Attempt parallel dispatch (Step 1.1 below): issue all 3 Agent calls in one message.
2. If the environment executes all 3 successfully: parallel mode confirmed. Proceed to post-dispatch handling.
3. If any Agent call errors with a **tool-availability or concurrency error** (e.g., "tool not found", "cannot dispatch multiple agents", "concurrent limit exceeded") — as opposed to a content/timeout error within the agent:
   - Store any results that DID return successfully.
   - Switch to **sequential mode** for the remaining personas that haven't returned.
   - Use the same prompts from Step 1.1 — just dispatch them one at a time.
4. If the Agent tool is completely unavailable on the first call: fall back to **Level 2** (single-agent inline) per the Graceful Degradation Plan in Phase 0.

**User-facing status messages:**
- Parallel: *"All 3 perspectives are being generated simultaneously..."*
- Sequential (on switch): *"Generating perspectives one at a time (parallel dispatch unavailable in this environment)..."*

### Step 1.1: Parallel Dispatch (Default)

Dispatch ALL THREE Agent calls in a **single message**. The prompts below follow the
template from `prompts/build_debate_query.md` but are fully inlined so this file is
self-contained. Each call is independent — they can run in any order.

**Agent call 1 — Methodology Critic:**

```
Agent tool call:
  prompt: |
    You are acting as: Methodology Critic

    Read the following persona definition carefully. It defines WHO you are,
    WHAT lens you apply, and HOW to structure your output.

    <persona>
    [Use Read tool to get: skills/ds-brainstorm/references/methodology-critic.md]
    [Paste the FULL contents of that file here]
    </persona>

    ## Analysis to Challenge

    [Paste the user's analysis question/plan here]

    ## Available Evidence

    [Paste the complete evidence_block assembled in Step 0.5]

    ## Instructions

    1. Read the analysis question carefully
    2. Apply your lens and attention directive to the evidence
    3. **Ground your understanding FIRST:** Before challenging, state the system components,
       pipeline stages, or metrics you are reasoning about. Include a `system_understanding`
       field in your output with `components`, `boundaries`, and `unknowns`.
       NEVER hypothesize about components you haven't explicitly named.
    4. **Execute your MANDATORY FIRST ACTIONS** from your persona definition before any other analysis
    5. **Check your PROHIBITED CONVERGENCE rules** — if you're drifting into another persona's lane, STOP and refocus
    6. Challenge the analysis plan from your perspective — do NOT agree easily
    7. Produce structured JSON output per your Output Format section
    8. Be specific: reference concrete evidence, name specific concerns, suggest specific alternatives
    9. If domain knowledge is available, ground your challenges in domain conventions
    10. Return ONLY the JSON output — no preamble, no explanation outside the JSON
```

**Agent call 2 — Stakeholder Advocate:**

```
Agent tool call:
  prompt: |
    You are acting as: Stakeholder Advocate

    Read the following persona definition carefully. It defines WHO you are,
    WHAT lens you apply, and HOW to structure your output.

    <persona>
    [Use Read tool to get: skills/ds-brainstorm/references/stakeholder-advocate.md]
    [Paste the FULL contents of that file here]
    </persona>

    ## Analysis to Challenge

    [Paste the user's analysis question/plan here]

    ## Available Evidence

    [Paste the complete evidence_block assembled in Step 0.5]

    ## Instructions

    1. Read the analysis question carefully
    2. Apply your lens and attention directive to the evidence
    3. **Ground your understanding FIRST:** Before challenging, state the system components,
       pipeline stages, or metrics you are reasoning about. Include a `system_understanding`
       field in your output with `components`, `boundaries`, and `unknowns`.
       NEVER hypothesize about components you haven't explicitly named.
    4. **Execute your MANDATORY FIRST ACTIONS** from your persona definition before any other analysis
    5. **Check your PROHIBITED CONVERGENCE rules** — if you're drifting into another persona's lane, STOP and refocus
    6. Challenge the analysis plan from your perspective — do NOT agree easily
    7. Produce structured JSON output per your Output Format section
    8. Be specific: reference concrete evidence, name specific concerns, suggest specific alternatives
    9. If domain knowledge is available, ground your challenges in domain conventions
    10. Return ONLY the JSON output — no preamble, no explanation outside the JSON
```

**Agent call 3 — Pragmatist:**

```
Agent tool call:
  prompt: |
    You are acting as: Pragmatist

    Read the following persona definition carefully. It defines WHO you are,
    WHAT lens you apply, and HOW to structure your output.

    <persona>
    [Use Read tool to get: skills/ds-brainstorm/references/pragmatist.md]
    [Paste the FULL contents of that file here]
    </persona>

    ## Analysis to Challenge

    [Paste the user's analysis question/plan here]

    ## Available Evidence

    [Paste the complete evidence_block assembled in Step 0.5]

    ## Instructions

    1. Read the analysis question carefully
    2. Apply your lens and attention directive to the evidence
    3. **Ground your understanding FIRST:** Before challenging, state the system components,
       pipeline stages, or metrics you are reasoning about. Include a `system_understanding`
       field in your output with `components`, `boundaries`, and `unknowns`.
       NEVER hypothesize about components you haven't explicitly named.
    4. **Execute your MANDATORY FIRST ACTIONS** from your persona definition before any other analysis
    5. **Check your PROHIBITED CONVERGENCE rules** — if you're drifting into another persona's lane, STOP and refocus
    6. Challenge the analysis plan from your perspective — do NOT agree easily
    7. Produce structured JSON output per your Output Format section
    8. Be specific: reference concrete evidence, name specific concerns, suggest specific alternatives
    9. If domain knowledge is available, ground your challenges in domain conventions
    10. Return ONLY the JSON output — no preamble, no explanation outside the JSON
```

**All three calls go in a single message.** The environment decides whether to run
them concurrently or serialize them — either way, you get all 3 results back before
proceeding.

### Step 1.2: Sequential Fallback (If Parallel Fails)

If Step 1.1 triggers a tool-availability or concurrency error (see Detection Logic above),
switch to sequential dispatch for any personas that haven't returned yet.

**Dispatch order:** Critic → Advocate → Pragmatist (skip any that already succeeded
in the parallel attempt).

Use the **exact same prompts** from Step 1.1 — the only difference is that you issue
one Agent call per message instead of three.

Between each sequential dispatch, tell the user which persona just completed:
- After Critic: *"Methodology Critic has weighed in. (1/3)"*
- After Advocate: *"Stakeholder Advocate has weighed in. (2/3)"*
- After Pragmatist: *"Pragmatist has weighed in. All three perspectives are in. Synthesizing..."*

### Step 1.3: Post-Dispatch Handling (Both Modes)

After all 3 agents return (whether via parallel or sequential), process each result:

**For each persona (critic_output, advocate_output, pragmatist_output):**

1. **Parse the response as JSON.** Store as `{persona}_output`.
2. **If the agent fails or times out:** Retry **once** with a shorter evidence block
   (trim search results to 2 findings per section instead of 3-5). This retry is always
   sequential (single Agent call) regardless of the original dispatch mode.
3. **If it fails again:** Set `{persona}_output` to the error stub:
   `{"status": "error", "perspective": "{persona_key}", "summary": "{Persona Name} unavailable — proceeding with remaining perspectives."}`
   and continue.

**After all results are collected:**
- If parallel mode succeeded: *"All three perspectives are in. Synthesizing..."*
- If sequential mode was used: the per-persona messages from Step 1.2 already informed the user.

### Error Summary for Phase 1

| Scenario | Action |
|----------|--------|
| Agent returns valid JSON | Store output, proceed |
| Agent returns non-JSON text | Try to extract JSON from the response; if impossible, wrap the text in `{"status": "warning", "summary": "[text]", "perspective": "...", "findings": []}` |
| Agent fails/times out | Retry once with reduced evidence (always sequential). If still fails, use error stub and proceed. |
| Parallel dispatch partially fails (tool error) | Store successful results, switch to sequential for remaining personas |
| 2 of 3 agents fail | Proceed with the 1 successful output. Note limitation to user. |
| All 3 agents fail | Abort Phase 1. Tell user: *"All three perspectives failed to generate. Try rephrasing your analysis question or running again."* |

---

## Phase 2: Cross-Persona Challenge Synthesis

**Goal:** The orchestrator (YOU, the agent executing this SKILL.md) reads all 3 subagent
outputs and produces a structured challenge for the user. This is NOT a consensus
summary — it's a debate brief that preserves tensions.

> **Why the orchestrator does this, not a subagent:** Synthesis requires seeing all 3
> outputs simultaneously. Dispatching a 4th subagent would waste context budget and add
> latency. The orchestrator already has all 3 outputs in context.

### Step 2.1: Read All Three Outputs

You already have `critic_output`, `advocate_output`, and `pragmatist_output` in context
from Phase 1. If any are error stubs, note which perspectives are missing.

### Step 2.2: Identify Agreements

Scan all 3 outputs for findings where perspectives align. Agreements are strong signals —
when a rigor expert, a business expert, and a feasibility expert all flag the same thing,
it almost certainly matters.

Look for:
- Same concern raised by 2+ personas (even if worded differently)
- Same recommendation appearing across outputs
- Same data gap or assumption flagged by multiple perspectives

Produce **2-3 agreement bullets**, each as a clear statement:
> *"All three perspectives agree that [X] is [assessment]."*

### Step 2.3: Identify Tensions

Scan for places where perspectives **disagree or pull in different directions**. These
are the most valuable outputs of the brainstorm — they surface real tradeoffs.

Stage each tension as an explicit back-and-forth exchange:
> *"Methodology Critic says: '[specific concern].' But Pragmatist counters: '[specific counterpoint].'
> This means you need to decide: [what the user must weigh]."*

Produce **2-3 tension exchanges**. Common tension patterns:
- Rigor vs. feasibility (Critic wants more controls; Pragmatist says data doesn't exist)
- Rigor vs. business framing (Critic wants statistical precision; Advocate wants simple story)
- Feasibility vs. business impact (Pragmatist says cut scope; Advocate says the cut version isn't compelling)

### Step 2.4: Frame the Key Question

Identify the **single most important tension** the user needs to resolve before
proceeding. Frame it as a direct question:

> *"Before we go further: [question]?"*

This question should be the one where the user's answer changes the direction of the
entire analysis. Good key questions force a tradeoff, not a yes/no.

### Step 2.5: Present the Synthesis to the User

Format the synthesis as a conversational challenge (not a report). Use this structure:

```
## Three Perspectives on Your Analysis

**Where the panel agrees:**
- [Agreement 1]
- [Agreement 2]
- [Agreement 3, if applicable]

**Where they clash:**

[Tension 1 — staged as exchange]

[Tension 2 — staged as exchange]

[Tension 3, if applicable — staged as exchange]

**The key question you need to answer:**

[Key question framed directly to the user]
```

Then wait for the user to respond. Do NOT proceed to Phase 3 automatically.

### Step 2.6: Context Trimming (before Socratic loop)

Before entering Phase 3, trim context to prevent attention degradation:

**Keep:**
- Each persona's structured JSON output (~3K per persona, ~9K total)
- The synthesis you just produced (agreements, tensions, key question)
- Domain knowledge and external knowledge summaries (reference material)
- The user's original question

**Trim (discard from active reasoning):**
- Raw search results from Phase 0 (URLs, snippets) — already distilled into evidence block
- Intermediate search queries and search grounding details
- Persona reference file contents (already consumed by subagents)

**Why:** By Phase 3, the raw search results (~30K tokens across 3 searches) have been
distilled into persona findings. Carrying them forward wastes attention budget and
causes models to skip phases or jump to conclusions (observed with GPT 5.4 high).

**How:** You don't need to literally delete context. Instead, when constructing Phase 3
responses, reference ONLY the persona JSON outputs and synthesis — not the raw evidence
block. If you need to re-check a specific evidence point, re-read it on demand.

---

## Phase 3: Socratic Dialogue Loop

**Goal:** Push the user to sharpen their analysis plan through conversational challenge.
You (the orchestrator) drive this loop using a unified "challenger" voice that draws on
all 3 persona outputs from Phase 1.

### Tracking State

Maintain a mental ledger of concerns from Phase 1 across two categories:
- **Addressed:** The user has responded to this concern substantively.
- **Unaddressed:** The user has not yet engaged with this concern.

Also track:
- `round_count`: starts at 1 after the user's first response to the synthesis
- `max_rounds`: from `--rounds` parameter (default: 3)

### Step 3.1: Process User Response

When the user responds to the synthesis (or to a previous Socratic push):

1. **Identify which concerns they addressed.** Move those to the "addressed" ledger.
2. **Identify which concerns they ignored or deflected.** Keep those in "unaddressed."
3. **Check for new threads.** Did the user's response introduce a fundamentally new
   direction that the original personas didn't assess?

### Step 3.2: Push Back

Construct your response using this logic:

**If the user addressed some concerns but not others:**
> *"Good — you've addressed [addressed concern]. But [persona name]'s point about [unaddressed concern] is still open: [restate the specific concern as a question]."*

**If the user addressed all raised concerns:**
> *"Strong responses. Let me push one level deeper: [follow-up question that tests the robustness of their answers, drawing on persona knowledge]."*

**If the user deflected or gave a vague answer:**
> *"I hear you, but that doesn't resolve [persona name]'s concern. Specifically: [restate with more precision]. What would you concretely do about this?"*

### Step 3.3: Re-invoke a Subagent (Rare, Only When Needed)

**When to re-invoke:** Only if the user fundamentally changes the analysis plan in a way
that invalidates the original persona assessment. Examples:
- User switches from A/B test to observational study (re-invoke Methodology Critic)
- User changes target audience entirely (re-invoke Stakeholder Advocate)
- User discovers a key data source doesn't exist (re-invoke Pragmatist)

**How to re-invoke:** Same `Agent` tool pattern as Phase 1, but with an updated prompt
that includes the original assessment AND the new information:

```
Agent tool call:
  prompt: |
    You are acting as: [persona_name]

    <persona>
    [Full contents of the persona reference file]
    </persona>

    ## Original Analysis Plan
    [Original analysis question]

    ## Your Previous Assessment
    [The persona's original JSON output from Phase 1]

    ## What Changed
    [Describe the specific change the user made]

    ## Updated Analysis Plan
    [The revised analysis plan based on the dialogue so far]

    ## Instructions
    1. Review your previous assessment in light of the change
    2. Produce an UPDATED structured JSON assessment
    3. Focus only on what changed — don't repeat concerns that are no longer relevant
    4. Return ONLY the JSON output
```

**Do NOT re-invoke all 3 subagents.** Only the one whose domain is affected by the change.

### Step 3.4: Check Termination Conditions

After each round, check whether to continue:

| Condition | Action |
|-----------|--------|
| User says "enough", "I'm good", "let's move on", "wrap up", or similar | Proceed to Phase 4 |
| `round_count >= max_rounds` | Tell user: *"That's {max_rounds} rounds. Want to keep going or wrap up?"* If they want more, continue. If not, proceed to Phase 4. |
| All major concerns addressed | Tell user: *"You've addressed the key tensions. Ready to wrap up with a summary?"* Proceed to Phase 4 on confirmation. |

Increment `round_count` after each completed exchange (user response + orchestrator push-back = 1 round).

---

## Phase 4: Structured Output

**Goal:** Produce a clean summary the user can reference later, in both human-readable
and machine-readable formats.

### Step 4.1: Human-Readable Summary

Present this directly in the conversation:

```
## Brainstorm Summary

### Analysis Question
[The user's analysis question, restated clearly — reflecting any refinements from the dialogue]

### Key Decisions Made
- [Decision 1 — what the user committed to during the debate]
- [Decision 2]
- [Decision 3]

### Open Questions
- [Question 1 — unresolved concerns that need further investigation]
- [Question 2]

### Recommended Next Steps
1. [Concrete action the user should take next]
2. [Second action]
3. [Third action, if applicable]

### Perspective Summary
| Perspective | Assessment | Top Concern |
|-------------|------------|-------------|
| Methodology Critic | [SOUND/CONCERNS/MAJOR_ISSUES] | [One-line top concern] |
| Stakeholder Advocate | [SOUND/CONCERNS/MAJOR_ISSUES] | [One-line top concern] |
| Pragmatist | [SOUND/CONCERNS/MAJOR_ISSUES] | [One-line top concern] |
```

### Step 4.2: Machine-Readable JSON

Produce the full structured output matching the observation contract from CLAUDE.md.
Show it to the user in a code block.

**Populating `search_context`:** Extract the structured search findings from the
evidence block assembled in Step 0.5. Map each evidence block section to its
corresponding array:
- "Domain Context" findings → `search_context.domain_signals`
- "Audience Signals" findings → `search_context.audience_signals`
- "Prior Art" findings → `search_context.prior_analyses`

Each array entry should be a concise string summarizing the finding with its source
URL. If a search returned no results, use an empty array `[]` for that field.
If search was skipped entirely (Level 1+ degradation), set all three arrays to `[]`.

```json
{
  // --- Top-level metadata (aligned with design doc contract) ---
  "brainstorm_id": "ds-brainstorm-{YYYY-MM-DD}-{short_slug}",
  "created_at": "ISO 8601 timestamp, e.g. 2026-03-22T14:30:00Z",
  "question": "the user's analysis question as refined during the dialogue",
  "domain": "domain name if --domain was used, otherwise null",
  "stakeholders": ["stakeholder names if --stakeholder was used, otherwise empty array"],
  "search_context": {
    "domain_signals": ["key findings from Search 1 (Domain Context) — 3-5 items with source URLs"],
    "audience_signals": ["key findings from Search 2 (Audience Signals) — 3-5 items with source URLs"],
    "prior_analyses": ["key findings from Search 3 (Prior Art) — 2-3 items with source URLs"]
  },

  // --- Perspectives: OBJECT keyed by persona name (not an array) ---
  // This matches the design doc schema where perspectives is an object,
  // enabling direct access via perspectives.methodology_critic instead of
  // iterating an array to find a specific persona.
  "perspectives": {
    "methodology_critic": {
      "status": "success|warning|error",
      "summary": "one-line assessment",
      "perspective": "methodology_critic",
      "assessment": "SOUND|CONCERNS|MAJOR_ISSUES",
      "findings": [
        {
          "type": "challenge|recommendation|concern",
          "severity": "critical|major|minor",
          "description": "specific finding text",
          "domain_reference": "relevant domain concept if applicable"
        }
      ],
      "next_actions": ["what the user should address"],
      "domain_references": ["specific domain concepts referenced"]
    },
    "stakeholder_advocate": {
      "status": "success|warning|error",
      "summary": "one-line assessment",
      "perspective": "stakeholder_advocate",
      "assessment": "SOUND|CONCERNS|MAJOR_ISSUES",
      "findings": [
        {
          "type": "framing_gap|narrative_suggestion|metric_mismatch",
          "severity": "critical|major|minor",
          "description": "specific finding text",
          "domain_reference": "relevant domain concept if applicable"
        }
      ],
      "framing_recommendation": "how to frame for max stakeholder impact",
      "narrative_hook": "the 30-second pitch",
      "key_metrics_for_audience": ["metrics execs would track"],
      "decision_this_enables": "what decision this analysis unlocks",
      "next_actions": ["what the user should address"],
      "domain_references": ["specific domain concepts referenced"]
    },
    "pragmatist": {
      "status": "success|warning|error",
      "summary": "one-line assessment",
      "perspective": "pragmatist",
      "assessment": "SOUND|CONCERNS|MAJOR_ISSUES",
      "findings": [
        {
          "type": "data_gap|scope_creep|timeline_risk|feasibility_concern",
          "severity": "critical|major|minor",
          "description": "specific finding text",
          "domain_reference": "relevant domain concept if applicable"
        }
      ],
      "feasibility": "HIGH|MEDIUM|LOW",
      "data_availability": "what data exists vs what is assumed",
      "estimated_effort": "realistic timeline estimate",
      "scope_recommendation": "what to cut or defer",
      "eighty_twenty": "the simplest valuable version",
      "next_actions": ["what the user should address"],
      "domain_references": ["specific domain concepts referenced"]
    }
  },
  "synthesis": {
    "agreements": ["where all 3 perspectives align"],
    "tensions": [
      {
        "persona_a": "methodology_critic",
        "position_a": "what they said",
        "persona_b": "pragmatist",
        "position_b": "what they countered",
        "user_resolution": "what the user decided, or null if unresolved"
      }
    ],
    "key_question": "the most important tension framed as a question",
    "key_question_resolved": true
  },
  "dialogue_history": [
    {
      "round": 1,
      "role": "challenger",
      "content": "the orchestrator's challenge text",
      "references_persona": "methodology_critic|stakeholder_advocate|pragmatist|synthesis"
    },
    {
      "round": 1,
      "role": "user",
      "content": "the user's response text",
      "concerns_addressed": ["list of concerns this response addressed"]
    }
  ],
  "outcome": {
    "decisions_made": ["key decisions from the dialogue"],
    "open_questions": ["unresolved concerns"],
    "next_steps": ["recommended actions"]
  }
}
```

### Step 4.3: Save JSON (Optional)

After showing the JSON, ask the user:
*"Want me to save this brainstorm output? I can write it to `outputs/ds-brainstorm-{YYYY-MM-DD}-{slug}.json`."*

If the user says yes, use the `Write` tool:
```
Write file: outputs/ds-brainstorm-{YYYY-MM-DD}-{slug}.json
Content: [the JSON object above]
```

If the user says no or doesn't respond, skip saving. The JSON is already visible in
the conversation.

---

## Checklist

- [ ] Scope check passed (single analysis question)
- [ ] Domain knowledge loaded (if `--domain` specified)
- [ ] Stakeholder profile loaded (if `--stakeholder` specified, with staleness check)
- [ ] Search grounding executed (or fallback flagged)
- [ ] Evidence block assembled
- [ ] Methodology Critic dispatched and returned
- [ ] Stakeholder Advocate dispatched and returned
- [ ] Pragmatist dispatched and returned
- [ ] Synthesis produced with agreements + tensions
- [ ] Socratic dialogue loop completed (user satisfied or max rounds)
- [ ] Human-readable summary produced
- [ ] Machine-readable JSON produced
