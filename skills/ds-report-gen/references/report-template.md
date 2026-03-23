# Report Template — Dual-Format Reference

This file defines the canonical formats for both the exec summary and the JSON
knowledge artifact. The report generator (SKILL.md) references this template
during Phase 1 to ensure consistent structure across all reports.

---

## Part A: Exec Summary Template

### Format

```markdown
# {Analysis Question — as a concise title}

## Key Finding

{1-2 sentences. The single most important thing the brainstorm revealed. This is
the "if you read nothing else" paragraph. Should be specific enough that a reader
knows whether to keep reading.}

## What Changed

{2-4 sentences. What shifted during the Socratic debate? What did the analyst
commit to that they hadn't planned originally? Pull specific moments from the
dialogue — e.g., "The team initially planned a full A/B test, but after the
Pragmatist flagged that traffic volume wouldn't support statistical power within
the quarter, shifted to an interleaving experiment."}

{Skip this section entirely if no dialogue_history exists. Do not fabricate
dialogue that didn't happen.}

## Recommended Approach

{3-5 sentences. The synthesized recommendation. Start with the what, then the why.
If the Pragmatist provided an 80/20 version, lead with that as the "start here"
and note the full version as a follow-on.

Structure: "We recommend [approach] because [rationale]. Start with [80/20 version]
to [quick win]. Once that validates, extend to [full scope]."}

## Open Questions

{Bulleted list. These are NOT weaknesses — they are legitimate unknowns that need
investigation before or during execution. Each question should be specific enough
that someone could go investigate it.}

- {Question 1 — with enough context that a reader understands why it matters}
- {Question 2}
- {Question 3, if applicable}

## Next Steps

{Numbered list. Concrete actions, each starting with a verb. Ordered by priority
or chronology. A reader should be able to hand this list to someone and say "do these."}

1. {Action 1 — specific, with a rough scope indicator if possible}
2. {Action 2}
3. {Action 3}
```

### Tone Guidance

**Do:**
- Write like you're briefing a VP who has 3 minutes between meetings
- Use concrete numbers and timeframes when available ("3-week effort" not "significant")
- Make the recommendation actionable — the reader should know what to DO
- Use "we" language — this is a team deliverable, not a solo opinion
- Pull one vivid quote or moment from the debate to make it feel grounded

**Don't:**
- Hedge with "it depends" or "further analysis needed" as the key finding
- Use DS jargon (p-values, NDCG, feature engineering) unless the audience profile
  confirms the reader uses these terms
- List every finding from every persona — synthesize into a narrative
- Include methodology details in the exec summary (that's what the JSON artifact is for)
- Pad with background context the reader already knows

### Length Targets

| Section | Target Length | Hard Limit |
|---------|-------------|------------|
| Key Finding | 1-2 sentences | 3 sentences max |
| What Changed | 2-4 sentences | 5 sentences max |
| Recommended Approach | 3-5 sentences | 6 sentences max |
| Open Questions | 2-4 bullets | 5 bullets max |
| Next Steps | 2-4 items | 5 items max |
| **Total** | **400-600 words** | **700 words absolute max** |

### Good vs Bad Examples

**Bad Key Finding:**
> "The brainstorm surfaced several interesting perspectives on the search relevance
> analysis. The Methodology Critic raised concerns about statistical rigor, while
> the Stakeholder Advocate suggested better framing. Further analysis is needed."

Why it's bad: Vague, hedging, no specific insight. A VP reads this and learns nothing.

**Good Key Finding:**
> "The proposed NDCG analysis won't land with leadership because it measures ranking
> quality, not user success. Reframing around query abandonment rate — which dropped
> 12% after the last ranking change — gives leadership a metric they already track
> and ties the analysis directly to the OKR."

Why it's good: Specific, actionable, connects to a real metric, tells the reader
what to change.

**Bad Recommended Approach:**
> "We recommend conducting a thorough analysis of search relevance metrics,
> considering both online and offline evaluation approaches, and presenting
> findings to stakeholders in an appropriate format."

Why it's bad: Says nothing. Every word could be removed and the meaning wouldn't change.

**Good Recommended Approach:**
> "We recommend an interleaving experiment comparing the current L2 ranker against
> the proposed cross-encoder variant, measured by query abandonment rate and
> time-to-click. Start with high-traffic navigational queries (60% of volume,
> lowest variance) to get signal within 2 weeks. If abandonment drops >5%,
> extend to informational queries in the following sprint."

Why it's good: Specific method, specific metrics, specific scope, specific timeline,
specific success criterion, specific next step.

---

## Part B: JSON Knowledge Artifact Schema

### Schema

```json
{
  "report_id": "ds-report-YYYY-MM-DD-slug",
  "brainstorm_id": "ds-brainstorm-YYYY-MM-DD-slug",
  "generated_at": "ISO-8601 timestamp",
  "format_version": "1.0",

  "analysis_question": {
    "original": "Copied from the brainstorm JSON's `question` field (a plain string)",
    "refined": "The question as refined during dialogue (null if unchanged) — scan dialogue_history for restatements"
  },

  "audience": {
    "name": "Stakeholder name or null",
    "profile_loaded": true,
    "key_priorities": ["From Layer 1, if profile loaded"],
    "metric_vocabulary": ["From Layer 3, if profile loaded"]
  },

  "claims": [
    {
      "claim": "A specific factual or analytical assertion",
      "source_persona": "methodology_critic | stakeholder_advocate | pragmatist | user | synthesis",
      "dialogue_round": 1,
      "confidence": "HIGH | MEDIUM | LOW",
      "supporting_evidence": "Reference to search context or domain knowledge",
      "challenged_by": "persona name or null",
      "resolution": "How it was resolved, or null if unresolved"
    }
  ],

  "evidence_cited": [
    {
      "source": "URL or description of the evidence source",
      "used_by": ["methodology_critic", "pragmatist"],
      "relevance": "Why this evidence mattered to the brainstorm"
    }
  ],

  "methodology": {
    "chosen_approach": "The methodology the user committed to",
    "alternatives_considered": ["Other approaches discussed and why they were rejected"],
    "key_tradeoff": "The main tradeoff the user accepted",
    "eighty_twenty": "The minimal viable version (from Pragmatist), or null"
  },

  "stakeholder_framing": {
    "narrative_hook": "The 30-second pitch (from Stakeholder Advocate)",
    "key_metrics": ["Metrics the audience cares about"],
    "decision_enabled": "What business decision this analysis unlocks",
    "framing_recommendation": "How to frame for maximum impact"
  },

  "open_questions": [
    {
      "question": "Specific unresolved question",
      "raised_by": "persona name",
      "severity": "critical | major | minor",
      "investigation_needed": "What would resolve this question"
    }
  ],

  "decisions": [
    {
      "decision": "What was decided",
      "rationale": "Why this was chosen",
      "dialogue_round": 2,
      "dissenting_view": {
        "persona": "pragmatist",
        "objection": "What they disagreed with",
        "resolution": "How the dissent was handled"
      }
    }
  ],

  "dialogue_summary": {
    "total_rounds": 3,
    "key_pivots": [
      {
        "round": 1,
        "description": "What changed in this round",
        "triggered_by": "The challenge or question that caused the shift"
      }
    ],
    "unaddressed_concerns": ["Concerns raised but never resolved in dialogue"]
  }
}
```

### Field-by-Field Mapping: Brainstorm JSON → Report Fields

This table shows where each report field comes from in the brainstorm output.

| Report Field | Brainstorm Source | Extraction Notes |
|-------------|-------------------|------------------|
| `analysis_question.original` | `question` | Direct copy — brainstorm output uses `question` (plain string), not `analysis_question` |
| `analysis_question.refined` | `dialogue_history` | Scan for user restating the question; null if unchanged |
| `claims[]` | `perspectives[].findings[]` + `dialogue_history[]` | Each finding becomes a claim; dialogue assertions are also claims |
| `evidence_cited[]` | `search_context` (cross-ref with perspective findings) | Only include evidence that a persona actually referenced |
| `methodology.chosen_approach` | `outcome.decisions_made` + Methodology Critic findings | Look for methodology-related decisions |
| `methodology.eighty_twenty` | Pragmatist perspective → `eighty_twenty` | Direct copy if present |
| `stakeholder_framing.*` | Stakeholder Advocate perspective | Direct copy of `narrative_hook`, `key_metrics_for_audience`, `decision_this_enables`, `framing_recommendation` |
| `open_questions[]` | `outcome.open_questions` + unresolved `synthesis.tensions` | Merge both sources; add severity from original findings |
| `decisions[]` | `outcome.decisions_made` + `dialogue_history` | Enrich with rationale from dialogue context and dissenting views from tensions |
| `dialogue_summary.key_pivots[]` | `dialogue_history` | Identify rounds where the user changed their position |
| `dialogue_summary.unaddressed_concerns` | `synthesis.tensions` where `user_resolution` is null | Direct extraction |

### Versioning

The `format_version` field allows downstream consumers to handle schema changes.
Current version: `1.0`. Increment the minor version for additive changes (new optional
fields). Increment the major version for breaking changes (renamed or removed fields).
