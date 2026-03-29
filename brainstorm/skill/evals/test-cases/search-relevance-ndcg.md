# Test Case: Search Relevance Metric Choice

**ID:** eval-001-search-relevance-ndcg
**Difficulty:** Easy
**Domain:** search-relevance (loaded via `--domain`)

## Input

```
/ds-brainstorm --domain search-relevance

Should we switch from NDCG@10 to MRR as our primary offline metric for Rovo search?
```

## Why This Is "Easy"

- Single, clear analysis question — no scope ambiguity
- The `search-relevance` domain file provides rich context about NDCG, MRR, QSR, and the full Rovo evaluation stack
- All 3 personas have concrete material to work with from the domain file
- No stakeholder profile, no timeline pressure — just a clean methodology question

## Expected Phase Flow

1. **Phase 0 (Scope Check):** PASS — single question about metric selection
2. **Phase 0 (Domain Load):** `references/domains/search-relevance.md` loaded into evidence block
3. **Phase 0 (Search Grounding):** Search for recent discourse on NDCG vs MRR tradeoffs, search evaluation best practices
4. **Phase 1 (Dispatch):** All 3 subagents dispatched (parallel by default, sequential fallback)
5. **Phase 2 (Synthesis):** Cross-persona synthesis with agreements and tensions
6. **Phase 3 (Socratic):** At least 1 round of challenger dialogue
7. **Phase 4 (Output):** Human-readable summary + machine-readable JSON

## Expected Persona Behavior

### Methodology Critic
Should challenge:
- Whether NDCG@10 and MRR measure the same thing (they don't — NDCG rewards graded relevance across all 10 positions; MRR only cares about the first relevant result)
- Position bias in the evaluation data — are your relevance labels affected by what users saw?
- Whether switching metrics changes what "good" looks like for the ranking model
- Whether offline metrics correlate with the online north-star (QSR)

Domain concepts expected: NDCG, MRR, QSR, position bias, graded relevance, offline vs online evaluation

### Stakeholder Advocate
Should challenge:
- Framing: execs care about query success rate (QSR), not NDCG vs MRR. How does this metric switch translate to user outcomes?
- What decision does this metric choice enable? If you switch to MRR, what changes in practice?
- Risk framing: switching primary metrics mid-stream can confuse stakeholders tracking dashboards

Domain concepts expected: QSR, query abandonment, user success, exec dashboards

### Pragmatist
Should challenge:
- Do you have the right relevance labels to compute both metrics? (graded labels for NDCG, binary for MRR)
- Can you run both metrics side-by-side before committing to a switch?
- What's the effort to rebaseline all existing experiments if you switch primary metric?
- Click log availability — do you have position data to debias?

Domain concepts expected: click logs, relevance labels, L1/L2 ranking layers, data availability

## Structural Checks (Pass/Fail Criteria)

### Observation Contract (per persona)
Each of the 3 subagent outputs must contain:

| Field | Type | Constraint |
|-------|------|------------|
| `status` | string | One of: `success`, `warning`, `error` |
| `summary` | string | Non-empty |
| `perspective` | string | Matches the persona key (`methodology_critic`, `stakeholder_advocate`, `pragmatist`) |
| `assessment` | string | One of: `SOUND`, `CONCERNS`, `MAJOR_ISSUES` |
| `findings` | array | Length >= 1 |
| `next_actions` | array | Length >= 1 |
| `domain_references` | array | Length >= 1 (domain is loaded, so personas MUST reference domain concepts) |

### Synthesis
| Field | Type | Constraint |
|-------|------|------------|
| `agreements` | array | Length >= 1 |
| `tensions` | array | Length >= 1 (there SHOULD be tension — Methodology Critic and Pragmatist likely disagree on evaluation rigor vs feasibility) |
| `key_question` | string | Non-empty — the single most important tension to resolve |

### Socratic Dialogue
| Field | Type | Constraint |
|-------|------|------------|
| `dialogue_history` | array | Length >= 2 (at minimum: 1 challenger message + 1 user response) |

Each dialogue entry must have:
| Field | Type | Constraint |
|-------|------|------------|
| `role` | string | `user` or `challenger` |
| `references_persona` | string or null | One of the 3 persona keys, or null |
| `round` | integer | >= 1 |
| `content` | string | Non-empty |

### Overall JSON
- The complete Phase 4 structured output must be valid, parseable JSON
- Must contain top-level keys: `brainstorm_id`, `created_at`, `question`, `perspectives`, `synthesis`, `dialogue_history`

## Quality Checks (v1.1)

Quality evals use the rubric in `evals/quality-rubric.md`. This section defines case-specific expectations per dimension.

### Dimension 1: Perspective Independence (minimum: 4)

**Why 4 is expected:** This is a clean methodology question where each persona has a natural, distinct angle:
- Methodology Critic should focus on what NDCG and MRR actually measure differently (graded relevance vs. first-hit) and whether switching changes what "good" means
- Stakeholder Advocate should reframe the question around QSR and user outcomes, not internal metric debates
- Pragmatist should ask about label availability (graded vs. binary) and rebaselining cost

**Failure indicators:** All 3 personas say "it depends on your use case" or all 3 recommend "run both side by side" without different reasoning. If the Methodology Critic and Stakeholder Advocate give the same advice, something is wrong -- they have fundamentally different lenses on metric choice.

### Dimension 2: Domain Grounding (minimum: 4)

**Why 4 is expected:** The search-relevance domain file provides rich vocabulary (NDCG, MRR, QSR, BM25, cross-encoder, L1/L2 ranking, position bias, click logs, offline vs. online evaluation). With this much domain material loaded, every persona should use domain terms in their actual findings, not just list them in domain_references.

**Specific grounding expectations:**
- Methodology Critic: should reference position bias, graded relevance, offline-online correlation
- Stakeholder Advocate: should translate to QSR, query abandonment, user success language
- Pragmatist: should ask about click log availability, position data for debiasing, label infrastructure

**Failure indicators:** Personas say "your metrics" or "the relevant metrics" instead of naming NDCG, MRR, QSR specifically. Domain_references array has terms but findings text reads like generic metric-switching advice.

### Dimension 3: Synthesis Quality (minimum: 3)

**Why 3 is the floor (not 4):** For a clean methodology question, there might be genuine consensus on some points (e.g., "run both metrics in parallel before switching"). The tension between rigor and feasibility is real but not as sharp as in the churn case. A score of 4+ is possible but not required.

**Expected tension:** Methodology Critic likely wants full debiasing and correlation analysis before switching; Pragmatist likely pushes for a simpler side-by-side comparison. This tension should appear in the synthesis.

**Failure indicators:** Synthesis says "all agree you should evaluate both metrics" without surfacing HOW they disagree on evaluation depth.

### Dimension 4: Socratic Challenge (minimum: 3)

**Why 3 is the floor:** This is a clean question where the user might have good answers. The Socratic loop should push on at least one unaddressed concern (e.g., "you addressed the metric tradeoff, but haven't said how you'd handle the rebaselining of past experiments").

**Failure indicators:** Challenger says "that's a good approach" after the user's first response without referencing any specific persona concern that wasn't addressed.

### Dimension 5: Actionability (minimum: 3)

**Why 3 is the floor:** The question is specific enough that next_actions should include concrete tasks (validate label types, run side-by-side on a sample, check NDCG-QSR correlation). But the question is also narrow enough that a full prioritized action plan (score 5) would be over-engineering.

**Expected actions:** At minimum, personas should suggest: (1) check what label types you have (graded vs. binary), (2) compute both metrics on existing eval sets, (3) check offline-online metric correlation.

**Failure indicators:** next_actions are all variants of "investigate further" or "talk to your team."

### Pass Criteria

- **Weighted average:** >= 3.5
- **Per-dimension minimums:** D1 >= 4, D2 >= 4, D3 >= 3, D4 >= 3, D5 >= 3
- **Both conditions must hold.** A weighted average of 3.6 with D2 = 2 is a FAIL.

---

## What This Eval Does NOT Check (Structural — v1.0)

- Whether the Methodology Critic's challenge is actually correct about NDCG vs MRR tradeoffs
- Whether the Stakeholder Advocate's framing advice would actually land with an exec
- Whether the Pragmatist's feasibility concerns are realistic for the user's actual data stack
