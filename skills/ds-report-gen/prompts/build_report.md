# Build Report Prompt Template

This template is used by the ds-report-gen orchestrator (SKILL.md) during Phase 1
to assemble the report from brainstorm JSON. The orchestrator inlines the variables
and follows these instructions to produce both report formats.

---

## Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `{BRAINSTORM_JSON}` | User input (pasted, file, or conversation context) | The complete structured output from ds-brainstorm Phase 4 |
| `{AUDIENCE_PROFILE}` | `stakeholders/{slug}.md` (if --audience specified) | The stakeholder profile, or empty string if not specified |
| `{FORMAT}` | `--format` flag (default: `dual`) | Which output(s) to produce: `exec`, `json`, or `dual` |

---

## Extraction Instructions

### How to pull key decisions from dialogue_history

The `dialogue_history` array is a chronological record of the Socratic debate.
Each entry has `role` (user or challenger), `round`, `content`, and metadata.

**To find decisions:**

1. Scan entries where `role = "user"` — these contain the analyst's commitments.
2. Look for commitment language: "I'll do X", "we should go with Y", "let's start with Z",
   "I agree that...", "you're right about...", "I'm dropping X in favor of Y".
3. Cross-reference with `concerns_addressed` field (if present) — this tracks which
   persona concerns the user responded to.
4. A decision is confirmed when the challenger does NOT push back on it in the
   following round — silence is acceptance.

**To find pivots (where the user changed direction):**

1. Compare the user's position in round N with their position in round N-1.
2. If they contradicted or revised a previous statement, that's a pivot.
3. Note what triggered the pivot — was it a challenger question? A specific persona's concern?

**To find unresolved threads:**

1. Look for challenger entries that reference a concern, followed by NO user response
   addressing that specific concern in any subsequent round.
2. Check `synthesis.tensions` where `user_resolution` is null — these are explicit unresolved items.

### How to synthesize persona perspectives into a coherent narrative

The three personas often pull in different directions. The report should synthesize
their views, not list them side by side.

**Synthesis approach:**

1. **Start with agreements.** If all three personas converge on something, that's your
   strongest signal. Lead with it.

2. **Resolve tensions through the user's decisions.** When Methodology Critic and
   Pragmatist disagree, check what the user decided. Present the decision, acknowledge
   the tradeoff: "We chose X over Y because [rationale], accepting the risk that [dissent]."

3. **Let unresolved tensions live in Open Questions.** Don't force consensus. If the
   Methodology Critic wanted an A/B test and the Pragmatist said traffic is too low and
   the user didn't resolve it — that's an open question, not a recommendation.

4. **Attribute without naming personas in the exec summary.** Instead of "The Methodology
   Critic said...", write "From a rigor standpoint..." or "On the feasibility side...".
   The JSON artifact carries full provenance; the exec summary carries the narrative.

5. **Use the Stakeholder Advocate's framing as the wrapper.** The narrative hook and
   metric vocabulary from the Stakeholder Advocate should shape HOW the findings are
   communicated, even if the substance comes from the Critic or Pragmatist.

### How to handle missing sections

| Missing Input | Exec Summary Impact | JSON Artifact Impact |
|---------------|--------------------|--------------------|
| No `dialogue_history` | Skip "What Changed" section. Add note: *"This report is based on persona analysis only — no Socratic dialogue was conducted."* | `dialogue_summary` has `total_rounds: 0` and empty arrays |
| No Methodology Critic | Note: *"Methodology perspective not available."* Lean on other perspectives. | `claims` array has no entries with `source_persona: "methodology_critic"` |
| No Stakeholder Advocate | Use generic business framing. Note: *"Stakeholder framing not available — using generic business language."* | `stakeholder_framing` fields are null or empty |
| No Pragmatist | Skip feasibility/scope sections. Note: *"Feasibility assessment not available."* | `methodology.eighty_twenty` is null |
| No `synthesis` | Synthesize inline from available perspectives. Will be less structured but still useful. | Reconstruct `claims` from perspective findings directly |
| No `outcome` | Extract what you can from dialogue. If no dialogue either, all outcome sections say "not captured." | `decisions` and `open_questions` are empty arrays |
| No `--audience` profile | Use generic business language throughout. No audience-specific metric vocabulary. | `audience.profile_loaded` is false, priority/vocabulary arrays empty |

---

## Assembly Sequence

When the orchestrator processes this template, it should follow this order:

### For exec summary:

1. Read the brainstorm JSON
2. Extract the analysis question (check for refinement in dialogue)
3. Identify the key finding (agreements first, then highest-severity finding)
4. Walk the dialogue for decisions and pivots
5. Synthesize the recommendation from outcomes + Pragmatist's 80/20
6. Collect open questions from outcomes + unresolved tensions
7. Format next steps as verb-first action items
8. If audience profile loaded: rewrite using stakeholder's metric vocabulary and priorities
9. Self-check word count (400-600 target)

### For JSON artifact:

1. Read the brainstorm JSON
2. Copy structural fields (brainstorm_id, question → analysis_question.original)
3. Extract claims from each perspective's findings with provenance
4. Cross-reference search_context with claims to build evidence_cited
5. Build methodology section from Critic findings + user decisions
6. Copy Stakeholder Advocate's framing fields
7. Merge open questions from outcome + unresolved tensions
8. Build decisions array with rationale and dissenting views
9. Summarize dialogue (total rounds, key pivots, unaddressed concerns)
10. Validate all required schema fields are present
