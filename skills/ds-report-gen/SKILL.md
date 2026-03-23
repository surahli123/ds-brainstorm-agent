---
name: ds-report-gen
description: >
  Transform brainstorm output into dual-format reports: a human-readable exec
  summary and a machine-readable JSON knowledge artifact. Consumes structured
  JSON from ds-brainstorm Phase 4. Use after a brainstorm to produce a polished
  deliverable or to archive brainstorm outcomes for future reference.
  Trigger: generate report, report, write up the brainstorm, exec summary.
---

# DS Report Generator — Dual-Format Report Builder

## Overview

Converts raw brainstorm output (the structured JSON from ds-brainstorm Phase 4)
into two complementary artifacts:

1. **Exec Summary** — A 400-600 word, VP-ready narrative. No jargon unless the
   audience speaks it. Structure: Question, Key Finding, What Changed, Recommended
   Approach, Open Questions, Next Steps.

2. **Knowledge Artifact** — A structured JSON object capturing claims, evidence,
   methodology decisions, stakeholder framing, and provenance (which persona said
   what, which dialogue round resolved it). Designed for downstream consumption:
   knowledge bases, future brainstorms, portfolio tracking.

**Why both?** The exec summary is for humans who need to act. The JSON artifact
is for machines (and future-you) who need to remember what was decided and why.

## Input

| Parameter | Required | Description |
|-----------|----------|-------------|
| Brainstorm JSON | Yes | Structured output from ds-brainstorm Phase 4. Accepted as: (a) pasted inline, (b) file path to a saved `.json`, or (c) the most recent brainstorm output visible in the conversation. |
| `--format` | No | `exec` (human-readable only), `json` (machine-readable only), `dual` (both). Default: `dual`. |
| `--audience` | No | Stakeholder name to tailor the exec summary framing. Loads profile from `stakeholders/{slug}.md` if it exists. Without this, the exec summary uses generic business language. |

## Constants

```
MAX_EXEC_WORDS: 600
MIN_EXEC_WORDS: 400
REPORTS_DIR: reports/
STAKEHOLDER_DIR: stakeholders/
```

---

## Phase 0: Input Parsing

**Goal:** Get the brainstorm JSON into memory and validate it has enough structure
to generate a report. Graceful degradation if the JSON is incomplete.

### Step 0.1: Locate the Brainstorm JSON

Check the three input sources in order of preference:

1. **File path provided:** User gave a path like `outputs/ds-brainstorm-2026-03-22-foo.json`.
   Use the `Read` tool to load it. If the file doesn't exist, tell the user and stop.

2. **Pasted inline:** User pasted JSON directly into the conversation. Parse it.

3. **Conversation context:** Look for the most recent brainstorm JSON output in the
   current conversation (Phase 4 output from ds-brainstorm). If found, use it.

If none of the above produces JSON, ask the user:
> "I need brainstorm output to generate a report. You can:
> 1. Paste the brainstorm JSON here
> 2. Give me a file path (e.g., `outputs/ds-brainstorm-2026-03-22-slug.json`)
> 3. Run `/ds-brainstorm` first and then come back"

### Step 0.2: Validate Required Fields

Check the brainstorm JSON for these required fields:

| Field | Required | Fallback if Missing |
|-------|----------|---------------------|
| `question` | Yes | Cannot proceed — ask user for the question |
| `perspectives` (array, >=1 entry) | Yes | Cannot proceed — need at least 1 perspective |
| `synthesis.agreements` | Preferred | Report will note "no cross-persona agreements identified" |
| `synthesis.tensions` | Preferred | Report will note "no tensions surfaced" |
| `dialogue_history` | Preferred | Exec summary skips "What Changed" section; JSON artifact has empty dialogue trail |
| `outcome.decisions_made` | Preferred | Report will note "no explicit decisions captured" |
| `outcome.open_questions` | Preferred | Report will note "no open questions recorded" |
| `outcome.next_steps` | Preferred | Report will note "no next steps defined" |

**Hard requirements:** `question` + at least 1 perspective. Everything else
degrades gracefully — the report will be thinner but still useful.

If validation fails on hard requirements:
> "This brainstorm output is missing [field]. I need at least a question
> and one perspective to generate a report. Can you provide the missing piece?"

If validation passes with gaps, note them internally and proceed. The report will
flag gaps explicitly rather than silently omitting sections.

### Step 0.3: Load Audience Profile (if --audience specified)

If `--audience` is provided:

1. Convert name to slug: lowercase, replace spaces with hyphens.
2. Read `stakeholders/{slug}.md` using the `Read` tool.
3. **If found:** Extract Layer 1 (OKRs/Priorities), Layer 3 (Metric Vocabulary),
   and Layer 5 (Risk Appetite) for framing the exec summary.
4. **If not found:** Warn the user:
   > "No stakeholder profile found for '{name}'. Run `/build-stakeholder-profile`
   > to create one. Generating report with generic business framing."
   Proceed without audience tailoring.

---

## Phase 1: Report Generation

**Goal:** Transform the brainstorm JSON into polished report artifacts. This phase
does the intellectual work — extracting decisions from dialogue, synthesizing persona
perspectives into a coherent narrative, and structuring provenance for the JSON artifact.

### Step 1.1: Generate Exec Summary (if --format is `exec` or `dual`)

Produce a markdown document following the template in `references/report-template.md`.

**Extraction logic — how to pull content from the brainstorm JSON:**

1. **Question:** Use `question` (a plain string from the brainstorm JSON). If it was
   refined during dialogue (check `dialogue_history` for the user restating or
   modifying the question), use the refined version and note the evolution.

2. **Key Finding:** Synthesize across all perspectives. What is the single most
   important thing the brainstorm revealed? Look for:
   - Unanimous agreements in `synthesis.agreements` (strongest signal)
   - The highest-severity finding across all perspectives
   - The resolution of the `synthesis.key_question` (if resolved)

3. **What Changed:** Walk `dialogue_history` chronologically. For each round, identify
   what the user committed to or shifted on. If `dialogue_history` is empty, skip
   this section with a note: *"No Socratic dialogue was conducted."*

4. **Recommended Approach:** Pull from `outcome.next_steps` + `outcome.decisions_made`.
   Synthesize into a coherent 2-3 sentence recommendation. If the Pragmatist's
   `eighty_twenty` field exists, use it as the basis for the "start here" recommendation.

5. **Open Questions:** Pull from `outcome.open_questions` + any unresolved tensions
   where `user_resolution` is null in `synthesis.tensions`.

6. **Next Steps:** Pull from `outcome.next_steps`. Make them concrete and actionable.
   Each step should start with a verb.

**Audience tailoring (if --audience profile loaded):**

- Replace generic business language with the stakeholder's metric vocabulary (Layer 3).
  Example: instead of "improve search quality," write "reduce query abandonment rate"
  if that's the metric the stakeholder tracks.
- Frame the key finding in terms of the stakeholder's priorities (Layer 1).
- Match the stakeholder's risk appetite (Layer 5): a "95% confidence" person gets
  caveats and confidence intervals mentioned; a "directional is fine" person gets
  bold recommendations without hedging.
- Do NOT invent metrics or priorities that aren't in the profile. Only use what's there.

**Tone rules:**

- Direct, no hedging (unless audience profile specifically shows they want caveats)
- First person plural ("we found," "our recommendation") — this is a team deliverable
- No DS jargon unless the audience profile shows the stakeholder uses it
- Specific over vague: "3-week effort" not "significant investment"
- Every claim should trace to a persona or dialogue round (but don't cite them
  formally — weave them in naturally)

**Length target:** 400-600 words. If it runs long, cut background context first,
then reduce the "What Changed" section. Never cut Open Questions or Next Steps.

### Step 1.2: Generate JSON Knowledge Artifact (if --format is `json` or `dual`)

Produce a structured JSON object following the schema in `references/report-template.md`.

**Extraction logic — provenance tracking:**

For every claim in the artifact, track:
- `source_persona`: which persona originated the claim
- `dialogue_round`: which round of Socratic dialogue confirmed or modified it (null if from Phase 1 only)
- `confidence`: HIGH (agreed by 2+ personas or confirmed by user), MEDIUM (single persona, not challenged), LOW (contradicted or unresolved)

**Field-by-field construction:**

1. **`report_id`**: `ds-report-{YYYY-MM-DD}-{slug}` where slug comes from the brainstorm_id
2. **`brainstorm_id`**: copied from input JSON
3. **`generated_at`**: current ISO timestamp
4. **`analysis_question`**: Build from the brainstorm's `question` field (a plain string). Set `analysis_question.original` to that string. Set `analysis_question.refined` by scanning `dialogue_history` for user restatements (null if unchanged).
5. **`audience`**: stakeholder name if --audience used, otherwise null
6. **`claims`**: array of specific factual or analytical claims made during the brainstorm.
   Extract from persona `findings` arrays + `dialogue_history` where the user or
   challenger made specific assertions.
7. **`evidence_cited`**: array of evidence references from the brainstorm's
   `search_context` that were actually used (not the full search dump — only what
   was referenced by a persona or in dialogue).
8. **`methodology`**: the methodology chosen or recommended. Pull from Methodology
   Critic's `findings` + Pragmatist's `eighty_twenty` + any dialogue where the
   user committed to a specific approach.
9. **`stakeholder_framing`**: the Stakeholder Advocate's recommended framing, narrative
   hook, and key metrics. Pull directly from that persona's output.
10. **`open_questions`**: unresolved items from `outcome.open_questions` + unresolved
    tensions.
11. **`decisions`**: array of decisions made during the brainstorm. Each entry includes
    `decision`, `rationale`, `dialogue_round` (when it was made), and `dissenting_view`
    (if a persona disagreed).

### Step 1.3: Quality Check

Before presenting to the user, self-review:

**Exec summary checks:**
- [ ] Word count is 400-600
- [ ] Every section header from the template is present (or explicitly noted as skipped with reason)
- [ ] No DS jargon that the audience wouldn't use (unless audience profile confirms they use it)
- [ ] At least one specific quote or reference from the dialogue (if dialogue_history exists)
- [ ] Next steps all start with verbs
- [ ] The recommendation is clear — a reader should know what to DO after reading this

**JSON artifact checks:**
- [ ] All required schema fields are present
- [ ] Every claim has `source_persona` provenance
- [ ] `decisions` array is non-empty (if `outcome.decisions_made` was non-empty)
- [ ] No null values in required fields (use empty arrays `[]` or empty strings `""` for optional fields with no data)

---

## Phase 2: Output

**Goal:** Present the report to the user and optionally save to disk.

### Step 2.1: Present to User

**If --format is `exec`:**
Present the exec summary as formatted markdown directly in the conversation.

**If --format is `json`:**
Present the JSON artifact in a code block.

**If --format is `dual` (default):**
Present the exec summary first (formatted markdown), then the JSON artifact in a
code block below it, separated by a clear divider:

```
[Exec summary in markdown]

---

<details>
<summary>Machine-Readable Knowledge Artifact (JSON)</summary>

[JSON in code block]

</details>
```

> **Why exec first?** The human-readable version is what the user will react to.
> The JSON is reference material — collapsible keeps focus on what matters.

### Step 2.2: Offer to Save

After presenting, ask:

> "Want me to save these reports? I can write:
> - Exec summary → `reports/{brainstorm_id}-summary.md`
> - JSON artifact → `reports/{brainstorm_id}-report.json`
>
> Save both, one, or neither?"

If the user says yes (to any combination):
1. Create the `reports/` directory if it doesn't exist
2. Write the requested file(s) using the `Write` tool
3. Confirm: *"Saved to `reports/{filename}`. You can reference this in future sessions."*

If the user says no or doesn't respond, skip saving. The report is already visible
in the conversation.

---

## Graceful Degradation

The report generator should produce useful output even with incomplete brainstorm data.

| Input State | Impact | Mitigation |
|-------------|--------|------------|
| Full brainstorm JSON (all fields populated) | Best quality | Happy path — no degradation |
| Missing `dialogue_history` | No "What Changed" section, no dialogue provenance | Skip section, note it. JSON artifact has empty dialogue trail. |
| Missing 1-2 perspectives | Thinner synthesis, fewer claims | Generate from available perspectives. Note which are missing. |
| Missing `synthesis` | No agreements/tensions to reference | Synthesize directly from perspective findings (do the synthesis inline). |
| Missing `outcome` | No decisions, open questions, or next steps | Extract what you can from dialogue_history. If no dialogue either, note all sections as "not captured." |
| Only `question` + 1 perspective | Minimal report | Generate a single-perspective summary. Clearly label it as partial. |
| Malformed JSON (partially parseable) | Some fields extractable | Extract what you can, warn user about what's missing, proceed. |

**Critical rule:** Never produce a report that hides gaps. If data is missing, SAY
it's missing. A report that looks complete but silently omits perspectives is worse
than one that explicitly says "Methodology Critic perspective: not available."

---

## Checklist

- [ ] Brainstorm JSON located (pasted, file path, or conversation context)
- [ ] Required fields validated (question + at least 1 perspective)
- [ ] Audience profile loaded (if --audience specified)
- [ ] Exec summary generated (if format includes exec)
- [ ] Exec summary word count checked (400-600)
- [ ] No unauthorized jargon in exec summary
- [ ] JSON artifact generated (if format includes json)
- [ ] Provenance tracked for all claims in JSON artifact
- [ ] Quality self-review passed
- [ ] Report presented to user
- [ ] Save option offered
- [ ] Files saved (if user approved)
